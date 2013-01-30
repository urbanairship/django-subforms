from django import forms

from subforms.decorators import ClassProperty


class HierarchicalFormBase(forms.Form):
    """Generic Form Base Class for nested forms."""
    @ClassProperty
    def subforms(cls):
        return cls.subform_config

    def __init__(self, data=None, files=None, *args, **kwargs):
        initial_data = kwargs.pop('initial', {})
        self.subform_instances = [
            (attr, form_class(
                data,
                files,
                prefix=attr, initial=initial_data.pop(
                    '%s-initial' % attr, None
                ),
                *args,
                **kwargs
            ))
            for attr, form_class in self.subform_config
        ]
        kwargs['initial'] = initial_data
        super(HierarchicalFormBase, self).__init__(data, files, initial=initial_data)
        # Used to differentiate which sub forms need to be validated.
        for attr, form in self.subform_config:
            self.fields[attr] = forms.BooleanField(
                required=False, widget=forms.HiddenInput
            )

    def is_valid(self):
        """Check the validity of each subform, and run crosscheck_forms."""
        is_valid = super(HierarchicalFormBase, self).is_valid()
        if not is_valid:
            return False

        for attr, form in self.subform_instances:
            if self.cleaned_data.get(attr):
                if not form.is_valid():
                    return False

        for attr, form in self.subform_instances:
            if self.cleaned_data.get(attr):
                # After we confirm that subform is valid
                # We convert the hidden boolean fields in the parent form
                # To be the cleaned_data of that subform, rather than
                # just a bool
                self.cleaned_data[attr] = form.cleaned_data

        return True

    def any_errors(self):
        """Check to see if there are any errors on any subforms."""
        return self.errors or any(
            [form.errors for attr, form in self.subform_instances]
        )
