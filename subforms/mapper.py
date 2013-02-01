# (c) 2013 Urban Airship and Contributors

class Mapper(object):
    """Creates a bidirectional mapper between model instances and form data.

    This is a helper class that introspects metadata attached to a
    ``django.form.Form`` class in order to create a mapping from
    a model instance to initial form data, as well as to apply
    ``cleaned_data`` back to a model instance (without saving it.)

    """
    def __init__(self, form_class, prefix=None):
        self.form_class = form_class
        self.prefix = prefix

        self.sub_maps = []

        if hasattr(form_class, 'subforms'):
            self.sub_maps = [
                Mapper(
                    subform_class, prefix
                ) for prefix, subform_class in form_class.subform_config
            ]

    def get_form_data(self, model_instance, prefix=None, _form_data=None):
        """Return form field data, if it exists, from the appropriate model.

        :param model_instance: ``django.models`` instance related to our form.
        :param prefix: str, prefix of the form we're mapping.
        :param _form_data: dict, any pre-existing form data.
        :rtype: dict

        """
        form_data = _form_data or {}
        prefix = '%s-' % prefix if prefix else ''

        # We're not a mappable form, just return whatever data was
        # passed in.
        if not hasattr(self.form_class, 'model_to_form') and not self.sub_maps:
            return form_data

        if hasattr(self.form_class, 'model_to_form'):
            for model_attr, form_attr in self.form_class.model_to_form:
                # if we supply a callable in our 'model_to_form', then
                # pass in our model_instance and return whatever value
                # our callable returns.
                if callable(model_attr):
                    model_value = model_attr(model_instance)
                else:
                    model_value = getattr(model_instance, model_attr, None)

                form_data[form_attr] = model_value

        if self.sub_maps:
            for sub_map in self.sub_maps:
                inst = model_instance
                # Check to see if there's a model instance path to follow
                # for a particular sub-form.
                #
                # Note: these should be ``@staticmethod`` on the parent
                # form class!
                key = 'instance_for_%s' % sub_map.prefix
                lookup = getattr(self.form_class, key, None)
                if lookup:
                    inst = lookup(inst)

                form_data[
                    '%s-initial' % (sub_map.prefix)
                ] = sub_map.get_form_data(inst, sub_map.prefix)

        return form_data

    def apply_form_data(self, form_data, model_instance, _instances=None):
        """Change attribute values on a model instance.

        Args:
            form_data: dict, cleaned data from our form.
            model_instance: the root ``django.models`` instance.
            instances: **private** a list of ``django.models``
                instances for sub forms to save.

        Returns:
            list of model instances to be saved.

        Note: does not save the models!

        """
        instances = _instances or [model_instance]
        form_to_model = getattr(self.form_class, 'form_to_model', None)
        if (not form_to_model and not self.sub_maps) or form_data is False:
            return instances

        if form_to_model:
            for form_attr, model_attr in self.form_class.form_to_model:
                value = form_data.get(form_attr)

                # Callable is responsible for setting value on inst.
                if callable(model_attr):
                    model_attr(model_instance, value)
                else:
                    setattr(model_instance, model_attr, value)

        for sub_map in self.sub_maps:
            # Assume using the same model_instance as parent form
            inst = model_instance
            # Use custom methods to return proper model instance if
            # defined.
            #
            # In general *avoid* using this method whenever possible.
            #
            # To avoid modifications to different versions of the same model
            # ALWAYS pass in a model.objects.select_related() version of the
            # object.
            # If the related object doesn't exist, it's the job of the
            # callable in the form to create it.

            # Note: these should be ``@staticmethod`` on the parent
            # form class!
            key = 'instance_for_%s' % sub_map.prefix
            lookup = getattr(self.form_class, key, None)
            if lookup:
                inst = lookup(inst)
                instances.append(inst)

            sub_map.apply_form_data(
                form_data.get(sub_map.prefix), inst, instances
            )

        return instances
