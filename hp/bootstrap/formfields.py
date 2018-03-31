# -*- coding: utf-8 -*-
#
# This file is part of the jabber.at homepage (https://github.com/jabber-at/hp).
#
# This project is free software: you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This project is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with this project. If
# not, see <http://www.gnu.org/licenses/>.

from django import forms
from django.contrib.auth import password_validation
from django.core.exceptions import FieldDoesNotExist
from django.forms.renderers import get_default_renderer
from django.forms.utils import flatatt
from django.utils.functional import Promise
from django.utils.html import mark_safe
from django.utils.translation import ugettext_lazy as _

from . import widgets


class BoundField(forms.boundfield.BoundField):
    """Overwrite BoundField to provide customised widget rendering and the formgroup() method.

    A BoundField is a form field in the context of a form.

    .. seealso:: https://docs.djangoproject.com/en/dev/ref/forms/api/#django.forms.BoundField
    """

    def formgroup_attrs(self):
        """HTML attributes for the top-level form-group div."""

        fg_attrs = dict(self.field.formgroup_attrs)
        fg_attrs.setdefault('id', 'fg_%s' % self.html_name)
        if fg_attrs.get('class'):
            fg_attrs['class'] += ' form-group'
        else:
            fg_attrs['class'] = 'form-group'

        if self.field.formgroup_class:
            fg_attrs['class'] += ' %s' % self.field.formgroup_class

        # If the form is bound, we add .was-validated for form validation
        if self.form.is_bound:
            fg_attrs['class'] += ' was-validated'

        if self.horizontal:
            fg_attrs['class'] += ' row'

        for error in self.errors.as_data():
            if error.code:
                fg_attrs['class'] += ' invalid-%s' % error.code
            else:
                fg_attrs['class'] += ' invalid-default'

        return flatatt(fg_attrs)

    @property
    def horizontal(self):
        return getattr(self.field, 'horizontal', True)

    def get_horizontal_wrapper_attrs(self):
        return self.field.get_horizontal_wrapper_attrs()

    @property
    def help_id(self):
        return 'hb_%s' % self.html_name

    @property
    def inline_help(self):
        return self.field.get_inline_help()

    def as_widget(self, *args, **kwargs):
        html = super().as_widget(*args, **kwargs)
        html += self.render_feedback()
        return html

    def build_widget_attrs(self, attrs, widget):
        attrs = super(BoundField, self).build_widget_attrs(attrs, widget)

        min_val_length = getattr(self.field, 'min_validation_length', False)
        if min_val_length is not False:
            attrs['data-min-validation-length'] = str(min_val_length)

        if self.help_text or self.errors:
            # Add the 'aria-describedby' attribute to the <input /> element. It's the id used by
            # the help-block describing the element and helps screen readers. See:
            #   http://getbootstrap.com/css/#forms-help-text
            attrs['aria-describedby'] = self.help_id

        return attrs

    def fmt_error_message(self, key, msg, **context):
        value = self.value()
        context['key'] = key
        context['value'] = value

        if hasattr(self.field, 'max_length'):
            context['max'] = self.field.max_length
        if isinstance(value, (str, Promise)):
            context['length'] = len(value)

        return msg % context

    def render_feedback(self):
        """Render the invalid-feedback messages.

        This tries to get all possible error messages from the model field and form field. The messages are
        used to by CSS to display the correct error message upon submission and by JS during form validation.
        """
        renderer = self.form.renderer or get_default_renderer()

        context = {
            'field_label': self.label,

            # We don't really need these so far
            'date_field_label': 'TODO_date_field_label',
            'lookup_type': 'TODO_lookup_type',
            'limit_value': 'TODO_limit_value',
        }
        invalid = {}

        # get model field validation messages first
        if hasattr(self.form, 'instance'):
            try:
                field = self.form.instance._meta.get_field(self.name)

                # update context for error message formatting
                context['model_name'] = self.form.instance._meta.verbose_name

                # extra field validators
                invalid.update({v.code: v.message for v in field.validators
                                if v.code in self.field.html_errors})

                # field error_messages
                invalid.update({k: self.fmt_error_message(k, v, **context)
                                for k, v in field.error_messages.items()
                                if k in self.field.html_errors})
            except FieldDoesNotExist:
                pass

        invalid.update({v.code: self.fmt_error_message(v.code, v.message, **context)
                        for v in self.field.validators if v.code in self.field.html_errors})
        invalid.update({k if k else 'default': self.fmt_error_message(k, v, **context)
                       for k, v in self.field.error_messages.items()
                       if k in self.field.html_errors})

        context = {
            'field': self,
            'valid': self.field.get_valid_feedback(),
            'invalid': invalid,
        }
        return mark_safe(renderer.render(self.field.feedback_template, context))

    def formgroup(self):
        renderer = self.form.renderer or get_default_renderer()
        context = {'field': self}
        return mark_safe(renderer.render(self.field.formgroup_template, context))

    def get_label_attrs(self):
        return self.field.get_label_attrs()

    def label_tag(self, contents=None, attrs=None, label_suffix=None):
        """Add the control-label and col-sm-2 class to label tags."""

        attrs = attrs or {}
        label_attrs = self.get_label_attrs()

        # Handle classes separately, so they are not overwritten
        label_classes = label_attrs.pop('class', None)
        if label_classes:
            if 'class' in attrs:
                attrs['class'] += ' %s' % label_classes
            else:
                attrs['class'] = label_classes

        return super(BoundField, self).label_tag(contents, attrs=attrs, label_suffix=label_suffix)


class BootstrapMixin(object):
    """Mixin that adds the form-control class used by bootstrap to input widgets."""

    add_success = True
    formgroup_class = None
    hide_label = False
    default_html_errors = {
        'invalid',
        'unique',
        'required',
    }

    # TODO: Rework this
    col_class = 'sm'
    label_cols = 2
    input_cols = 10

    horizontal = True
    """Display this field as a horizontal form group."""

    inline_help = False
    """Set to True to display help block inline."""

    min_validation_length = False
    """Start JavaScript validation at the given length."""

    valid_feedback = None

    formgroup_template = 'bootstrap/forms/formgroup.html'
    feedback_template = 'bootstrap/forms/feedback.html'

    def __init__(self, **kwargs):
        self.formgroup_attrs = kwargs.pop('formgroup_attrs', {})

        if 'horizontal' in kwargs:
            self.horizontal = kwargs.pop('horizontal')

        if 'add_success' in kwargs:
            self.add_success = kwargs.pop('add_success')

        if 'min_validation_length' in kwargs:
            self.min_validation_length = kwargs.pop('min_validation_length')

        self.valid_feedback = self._handle_feedback('valid_feedback', kwargs)

        html_errors = kwargs.pop('html_errors', set())
        for c in reversed(self.__class__.__mro__):
            html_errors |= getattr(c, 'default_html_errors', set())
        html_errors |= html_errors or set()
        self.html_errors = html_errors

        self.label_cols = kwargs.pop('label_cols', self.label_cols)
        self.input_cols = kwargs.pop('input_cols', self.input_cols)
        self.col_class = kwargs.pop('col_class', self.col_class)
        self.hide_label = kwargs.pop('hide_label', self.hide_label)

        super(BootstrapMixin, self).__init__(**kwargs)

    def _handle_feedback(self, key, kwargs):
        cls_value = getattr(self, key, None)

        # sanitize class attribute
        if cls_value is None:
            cls_value = {}
        if isinstance(cls_value, (Promise, str)):  # Promise == translated string
            cls_value = {'default': cls_value, }
        else:
            cls_value = cls_value.copy()

        value = kwargs.pop(key, {})
        if isinstance(value, (Promise, str)):  # Promise == translated string
            value = {'': value, }
        cls_value.update(value)

        return cls_value

    def get_inline_help(self):
        return self.inline_help

    def get_valid_feedback(self):
        return self.valid_feedback

    def get_input_grid_class(self):
        raise Exception('deprecated')
        return 'col-%s-%s' % (self.col_class, self.input_cols)

    def get_input_grid_attrs(self):
        raise Exception('deprecated')
        return {'class': self.get_input_grid_class()}

    def get_horizontal_wrapper_attrs(self):
        classes = 'col-%s-%s' % (self.col_class, self.input_cols)
        return {'class': classes}

    def get_label_attrs(self):
        """Get attributes for the label tag."""

        cls = []
        if self.hide_label is True:
            cls.append('sr-only')

        if self.horizontal:
            cls.append('col-%s-%s' % (self.col_class, self.label_cols))
            cls.append('col-form-label')

        return {'class': ' '.join(cls)}

    def get_bound_field(self, form, field_name):
        return BoundField(form, self, field_name)


class BootstrapCharField(BootstrapMixin, forms.CharField):
    widget = widgets.BootstrapTextInput


class BootstrapTextField(BootstrapMixin, forms.CharField):
    widget = widgets.BootstrapTextarea


class BootstrapEmailField(BootstrapMixin, forms.EmailField):
    widget = widgets.BootstrapEmailInput

    def clean(self, value):
        value = super(BootstrapEmailField, self).clean(value)
        if value:
            value = value.lower()
        return value


class BootstrapPasswordField(BootstrapMixin, forms.CharField):
    widget = widgets.BootstrapPasswordInput
    add_success = False

    def __init__(self, *args, **kwargs):
        if kwargs.pop('add_min_length', False):
            for validator in password_validation.get_default_password_validators():
                if isinstance(validator, password_validation.MinimumLengthValidator):
                    kwargs.setdefault('min_length', validator.min_length)
                    break
        super(BootstrapPasswordField, self).__init__(*args, **kwargs)


class BootstrapChoiceField(BootstrapMixin, forms.ChoiceField):
    widget = widgets.BootstrapSelect


class BootstrapModelChoiceField(BootstrapMixin, forms.ModelChoiceField):
    widget = widgets.BootstrapSelect


class BootstrapFileField(BootstrapMixin, forms.FileField):
    default_error_messages = {
        'mime-type': _('Upload a file with the correct type.'),
    }
    widget = widgets.BootstrapFileInput

    def __init__(self, *args, mime_types=None, **kwargs):
        mime_types = set()
        for c in reversed(self.__class__.__mro__):
            mime_types |= getattr(c, 'default_mime_types', set())
        mime_types |= mime_types or set()
        self.mime_types = mime_types

        super().__init__(*args, **kwargs)

    def clean(self, value, initial=None):
        value = super().clean(value, initial=initial)
        if value and self.mime_types and value.content_type not in self.mime_types:
            raise forms.ValidationError(self.error_messages['mime-type'] % {
                'value': value.content_type,
            }, code='mime-type')
        return value

    def widget_attrs(self, widget):
        attrs = super().widget_attrs(widget)
        if self.mime_types:
            attrs['accept'] = ','.join(self.mime_types)
        return attrs
