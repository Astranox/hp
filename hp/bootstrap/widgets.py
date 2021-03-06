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

import re

from django import forms

from .utils import clean_class_attrs


class BootstrapWidgetMixin(object):
    css_classes = ''
    """CSS classes to be added to this element."""

    def __init__(self, attrs=None, css_classes='', **kwargs):
        attrs = attrs or {}
        self._add_class(attrs, 'form-control')

        # handle css_classes
        for cls in self.__class__.mro():
            css_classes += ' %s' % getattr(cls, 'css_classes', '')
        css_classes = re.sub(' +', ' ', css_classes).strip()
        if css_classes:
            self._add_class(attrs, css_classes)

        super(BootstrapWidgetMixin, self).__init__(attrs=attrs, **kwargs)

    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs=extra_attrs)
        clean_class_attrs(attrs)
        return attrs

    def _add_class(self, attrs, cls):
        if attrs.get('class'):
            attrs['class'] += ' %s' % cls
        else:
            attrs['class'] = cls

    class Media:
        css = {
            'all': ('bootstrap/css/bootstrap.css', ),
        }
        js = (
            'bootstrap/js/bootstrap.js',
        )


class MergeClassesMixin(object):
    """Mixin to merge CSS classes from runtime and from the instances class attributes.

    This is most commonly used in MultiWidgets children, where extra_args contains the CSS classes from the
    parent widget.
    """

    def build_attrs(self, base_attrs, extra_attrs=None):
        if extra_attrs is None or 'class' not in base_attrs or 'class' not in extra_attrs:
            return super().build_attrs(base_attrs, extra_attrs=extra_attrs)

        extra_attrs['class'] = '%s %s' % (base_attrs.pop('class', ''), extra_attrs.pop('class', ''))
        return super().build_attrs(base_attrs, extra_attrs=extra_attrs)


class BootstrapMultiWidget(BootstrapWidgetMixin, forms.MultiWidget):
    template_name = 'bootstrap/forms/widgets/multiwidget.html'


class BootstrapTextInput(BootstrapWidgetMixin, forms.TextInput):
    template_name = 'bootstrap/forms/widgets/text.html'


class BootstrapTextarea(BootstrapWidgetMixin, forms.Textarea):
    pass


class BootstrapEmailInput(BootstrapWidgetMixin, forms.EmailInput):
    template_name = 'bootstrap/forms/widgets/text.html'


class BootstrapPasswordInput(BootstrapWidgetMixin, forms.PasswordInput):
    template_name = 'bootstrap/forms/widgets/password.html'

    def build_attrs(self, base_attrs, extra_attrs=None):
        if self.is_required:
            base_attrs['required'] = ''
        return super().build_attrs(base_attrs, extra_attrs=extra_attrs)


class BootstrapSetPasswordInput(BootstrapPasswordInput):
    css_classes = 'set-password'


class BootstrapConfirmPasswordInput(BootstrapPasswordInput):
    css_classes = 'confirm-password'


class BootstrapSelect(BootstrapWidgetMixin, forms.Select):
    css_classes = 'custom-select'


class BootstrapFileInput(BootstrapWidgetMixin, forms.ClearableFileInput):
    template_name = 'bootstrap/forms/widgets/file_input.html'
    css_classes = 'custom-file-input'

    def build_attrs(self, base_attrs, extra_attrs=None):
        # remove form-control
        base_attrs['class'] = base_attrs['class'].replace('form-control', '')
        return super().build_attrs(base_attrs, extra_attrs=extra_attrs)


class BootstrapCheckboxInput(BootstrapWidgetMixin, forms.CheckboxInput):
    css_classes = 'form-check-input'

    def build_attrs(self, base_attrs, extra_attrs=None):
        # remove form-control
        base_attrs['class'] = base_attrs['class'].replace('form-control', '')
        return super().build_attrs(base_attrs, extra_attrs=extra_attrs)
