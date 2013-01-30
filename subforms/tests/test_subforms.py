from django import forms

import unittest

from subforms.decorators import ClassProperty
from subforms.mapper import Mapper


class SubFormWithMapping(forms.Form):
    fake_title = forms.CharField(required=False)
    fake_field = forms.CharField(required=False)

    form_to_model = (
        ('fake_field', 'fake_field'),
        ('fake_title', 'fake_title'),
    )
    model_to_form = (
        ('fake_field', 'fake_field'),
        ('fake_title', 'fake_title'),
    )

class OtherSubFormWithMapping(forms.Form):
    fake_data = forms.CharField(required=False)

    form_to_model = (
        ('fake_data', 'fake_data'),
    )

    model_to_form = (
        ('fake_data', 'fake_data'),
    )


class SubFormWithNoMapping(forms.Form):
    fake_field = forms.CharField(required=False)


class FakeForm(forms.Form):
    name = forms.CharField(required=False)
    subform_config = (
        ('test_mapping', SubFormWithMapping),
        ('test_no_mapping', SubFormWithNoMapping),
    )

    @ClassProperty
    def subforms(cls):
        return dict(cls.subform_config)

    form_to_model = (
        ('name', 'item_name'),
    )

    model_to_form = (
        ('item_name', 'name'),
    )


class FakeModel(object):
    item_name = ''


class TestFormMapper(unittest.TestCase):

    def test_create_subform_mappings(self):
        """Make sure that mapper properly creates subforms at init."""
        # Ensure that sub maps are created for sub forms.
        fake_mapper = Mapper(FakeForm)
        self.assertEqual(len(fake_mapper.sub_maps), 2)
        # Order is preserved
        self.assertEqual(
            fake_mapper.sub_maps[0].form_class.__name__,
            'SubFormWithMapping'
        )
        self.assertEqual(
            fake_mapper.sub_maps[1].form_class.__name__,
            'SubFormWithNoMapping'
        )

        # Recursion has only gone one level.
        for sub_map in fake_mapper.sub_maps:
            self.assertEqual(
                len(sub_map.sub_maps),
                0
            )

        # If we create a mapping of a form without subforms,
        # ensure that no sub_maps are created.
        fake_mapper2 = Mapper(SubFormWithMapping)
        self.assertEqual(len(fake_mapper2.sub_maps), 0)

    def test_get_form_data(self):
        """Get model data for form fields using our mapping."""
        expected_output = {
            'name': 'Database',
            'test_no_mapping-initial': {},
            'test_mapping-initial': {
                'fake_field': 'Something unexpected',
                'fake_title': None,
            },
        }

        fake_mapper = Mapper(FakeForm)
        fake_model = FakeModel()
        fake_model.item_name = 'Database'
        fake_model.fake_field = 'Something unexpected'
        fake_initial_form_data = fake_mapper.get_form_data(fake_model)

        # Our form field name (as we expect it) equals our model attribute.
        self.assertEqual(fake_initial_form_data, expected_output)

    def test_get_form_data_as_callable(self):
        """Use callable instead of static definition of form field."""
        fake_model_value = 'Fun Test Data'

        def get_model_attr(model_inst):
            """Pretend we're looking up model data from another model."""
            return fake_model_value

        class FakeFormWithCallable(forms.Form):
            something = forms.CharField(required=False)
            model_to_form = ((get_model_attr, 'something'),)
            form_to_model = (('something', get_model_attr),)

        fake_mapper = Mapper(FakeFormWithCallable)
        fake_model = FakeModel()
        fake_model.database = fake_model_value

        fake_form_data = fake_mapper.get_form_data(fake_model)

        self.assertEqual(
            fake_form_data['something'],
            fake_model_value
        )

    def test_apply_form_data(self):
        """Make sure that form data changes our model inst. data."""
        fake_mapper = Mapper(FakeForm)
        fake_model = FakeModel()
        fake_model.item_name = ''
        fake_mapped_field = 'Something fake'
        fake_mapped_title = 'A Terrible Beginning'
        fake_unmapped_field = 'Will never see the light of day.'
        fake_form_data = {
            # Parent form
            'name': 'Something new!',
            # Sub form with mapping
            'test_mapping': {
                'fake_field': fake_mapped_field,
                'fake_title': fake_mapped_title,
            },
            # Sub form without mapping (doesn't get applied)
            'test_no_mapping': {
                'fake_field': fake_unmapped_field,
            },
        }
        instances = fake_mapper.apply_form_data(fake_form_data, fake_model)

        # We should have only modified the model which we passed in.
        self.assertEqual(len(instances), 1)
        # Test that these reference the same object
        self.assertEqual(instances[0], fake_model)

        # Parent form field's mapping updates the model:
        self.assertEqual(fake_model.item_name, fake_form_data['name'])
        # Sub form's mapping updates the model:
        self.assertEqual(fake_model.fake_field, fake_mapped_field)
        self.assertEqual(fake_model.fake_title, fake_mapped_title)

    def test_apply_form_data_as_callable(self):
        """Make sure form values sent to callable update model."""
        fake_form_value = 'This is some new data'

        def set_model_value(model_inst, value):
            """Pretend we're looking up "form" data from another model."""
            model_inst.database = value

        class FakeFormWithCallable(forms.Form):
            something = forms.CharField(required=False)
            model_to_form = ((set_model_value, 'something'),)
            form_to_model = (('something', set_model_value),)

        fake_mapper = Mapper(FakeFormWithCallable)
        fake_model = FakeModel()
        fake_model.database = ''
        form_data = {'something': fake_form_value}

        fake_instances = fake_mapper.apply_form_data(form_data, fake_model)
        self.assertEqual(len(fake_instances), 1)
        fake_instance = fake_instances[0]
        self.assertEqual(fake_instance.database, fake_form_value)

    def test_multiple_sub_forms_one_model(self):
        """Ensure two sub forms modifying the same 'model' don't drop data."""
        fake_form_value = 'This is some new data'
        class FakeFormWithSubForms(forms.Form):
            something = forms.CharField(required=False)
            model_to_form = (('something_else', 'something'),)
            form_to_model = (('something', 'something_else'),)
            # The same form validation mapped onto two separate
            # subforms.
            subform_config = (
                ('subform1', SubFormWithMapping),
                ('subform2', OtherSubFormWithMapping),
            )

            @ClassProperty
            def subforms(cls):
                return dict(cls.subform_config)

        fake_mapper = Mapper(FakeFormWithSubForms)
        fake_model = FakeModel()
        fake_field = 'Whaaaat'
        fake_title = 'Crrrrrrazy'
        fake_data = 'Yellow'
        form_data = {
            'something': fake_form_value,
            'subform2': {'fake_data': fake_data},
            'subform1': {'fake_field': fake_field, 'fake_title': fake_title},
        }

        fake_instances = fake_mapper.apply_form_data(form_data, fake_model)

        # Make sure we're still working with the same model instance.
        self.assertEqual(fake_instances[0], fake_model)

        # Saved from subform 2
        self.assertEqual(fake_model.fake_field, fake_field)
        # Saved from subform 1
        self.assertEqual(fake_model.fake_data, fake_data)
        self.assertEqual(fake_model.fake_title, fake_title)

    def test_instance_for_behavior(self):
        """Ensure transitioning between models from form -> subform works.

        Note: we also test what happens when two subforms specify the same
        model (they should create two separate instances of the model). This
        behavior is probably rarely desired, but is how the system works as
        constructed.

        """

        class OtherModel(object):
            """Model to be transitioned to from FakeModel."""
            pass

        def return_other_model(parent_model_inst):
            try:
                result = parent_model_inst.other_model
            except AttributeError:
                result = OtherModel()

            return result

        class FakeFormWithSubForms(forms.Form):
            something = forms.CharField(required=False)
            model_to_form = (('something_else', 'something'),)
            form_to_model = (('something', 'something_else'),)
            # The same form validation mapped onto two separate
            # subforms.
            subform_config = (
                ('subform1', SubFormWithMapping),
                ('subform2', SubFormWithMapping),
            )

            # model to test that we don't stomp on our changes.
            @staticmethod
            def instance_for_subform1(parent_model_inst):
                return return_other_model(parent_model_inst)

            @staticmethod
            def instance_for_subform2(parent_model_inst):
                return return_other_model(parent_model_inst)

            @ClassProperty
            def subforms(cls):
                return dict(cls.subform_config)

        fake_mapper = Mapper(FakeFormWithSubForms)
        fake_model = FakeModel()
        fake_field = 'What is the meaning of this!?'
        fake_title = 'Canterbury Tales'
        form_data = {
            'subform2': {'fake_title': fake_title},
            'subform1': {'fake_field': fake_field},
        }

        # This call should result in other_model being created and set as an
        # attr on our fake_model
        fake_instances = fake_mapper.apply_form_data(form_data, fake_model)

        # There'll be one for each form in this case.
        self.assertEqual(len(fake_instances), 3)

        fake_sub1 = fake_instances[1]
        fake_sub2 = fake_instances[2]

        # As nice as it would be to have these data merged into one
        # instance, it's not easily doable, so we save into separate
        # instances and leave implementation to the caller.
        self.assertEqual(fake_sub1.fake_field, fake_field)
        self.assertEqual(fake_sub2.fake_title, fake_title)
