***************
Django Subforms
***************

This project has two major logical section:

- mapper
- hierarchical forms

The Mapper is a requirement for the hierarchical form logic to work properly.
So we'll discuss how it works first. Then we'll discuss the use-case for
hierarchical forms.

Django Form Mapper
==================

Purpose
^^^^^^^

We developed the django form mapper as part of a project to enable us to
easily combine multiple forms into a single form entity, and to be able
to cross reference data entered into these subforms with ease. The form
mapper is a necessary requirement for us to programactically handle
arbitrary nesting of hierarchical forms.

An added benefit to this mode is that we can maintain isolated interests
in our views, models and forms. The guiding philosophy for this form
framework is that forms are only for validating and possibly
pre-processing form data from the client, nothing more.

Instead we rely on our mapper to peform the appropriate mutations on our
model instances, and give the view a chance to implement logic to
investigate these saved values for any final validation or modification
before finally saving the model instances.


Simple Example
^^^^^^^^^^^^^^

This example shows how to use simple mapping between a form and a model.
Most of the logic for what's getting saved is now in the view.

.. sourcecode::

    class BlogModel(models.Model):
        body = models.TextField()
        author = models.TextField()

    class BlogPostForm(forms.Form):
        text = forms.TextField()
        author = forms.CharField()

        model_to_form = (
            ('body', 'text'),
            ('author, 'author'),
        )

        form_to_model = (
            ('text', 'body'),
            ('author', 'author'),
        )

    def view(request, slug=None):
        blog_instance = Blog.objects.get(slug=slug) if slug else None
        mapper = Mapper(BlogPostForm)

        # grab initial data from the instance
        initial = mapper.get_from_model(blog_instance)

        form = BlogPostForm(initial=initial)
        if request.method == 'POST':
            form = BlogPostForm(
                request.POST, request.FILES
            )
            if form.is_valid():
                model_instances = mapper.apply_to_model(
                    form.cleaned_data, blog_instance
                )
                # and remember, you're responsible for saving the model!
                for inst in model_instances:
                    inst.save()

                return redirect('.')

        return render_to_response(
            'blog/edit.html',
            context={'form':form},
            context_instance=RequestContext(request)
        )


Core Features
^^^^^^^^^^^^^

While the mapper is absolutely required for subform processing, it can also be useful
for non-hierarchical forms. In the circumstances in which there are staright-forward
manipulations which need to be applied to/from the models in question.

Mapping
"""""""

Mapping itself is a simple syntax. Either mapping is optional, but you'll need at least
one for our mapping object to do anything.

The section above which declares the ``model_to_form`` and ``form_to_model`` is where
all the declaritive logic for our mapping lives, with the form itself.

.. sourcecode::

        model_to_form = (
            ('body', 'text'),
            ('author, 'author'),
        )

        form_to_model = (
            ('text', 'body'),
            ('author', 'author'),
        )


.. note::
    ``model_to_form`` and ``form_to_model`` are both optional and take a tuple of tuples
    where the inner tuples are the attribute names from the lhs and rhs respectively.


Callables in Attribute Mapping
""""""""""""""""""""""""""""""

While mapping is handy, sometimes you arent' simply setting a string attribute on a model.
At times you need to call a function, or setup some conditional logic in order to decide
how your form data will be seriealized. We do this using ``callables`` instead of naked
strings in our mapping.

For example:

.. sourcecode::

    def get_body(blog_instance):
        return blog_instance.get_body()

    def set_body(blog_instance, body):
        blog_instance.body = body

    model_to_form = (
        (get_body, 'text'),
        ('author', 'author'),
    )

    form_to_model = (
        ('text', set_body),
        ('author', 'author'),

    )


In this circumstance, you'll note that ``get_body`` and ``set_body`` aren't strings, but function names. These will need to be functions which are in the scope of the Form you're going to be calling them.

.. note:: Generally, you'll only need to use callables on the left hand side for ``model_to_form``
    and on the right hand side for ``form_to_model``, leaving any modification of form data to
    the form's clean methods.

Multiple Model Instances
""""""""""""""""""""""""

You might have noticed in our example above with the way that our mapper returned a list of
model instances, even when we only passed in a single model.

This is because we deal with forms that save fields to multiple model types by specifying
subforms for each type of model. We delegate which subform gets which model instance in the
parent form using ``instance_for_<form prefix>`` callables. These callables take the parent
form's model instance as input and return the relevant model instance for the subform matching
``<form prefix>``.

.. sourcecode::

    @staticmethod
    def instance_for_blog_body(blog_instance):
        """Returns a blog body instance for a blog_instance."""
        return models.BlogBody.objects.get_or_create(
            blog=blog_instance
        )

.. warning:: ``instance_for_<form prefix>`` methods must be static methods!

Now let's see how these features work in more complex examples!


Complex Example
^^^^^^^^^^^^^^^

In our parent form, the ``instance_for`` definition:

.. sourcecode::

    @staticmethod
    def instance_for_blog_tag(blog):
        """Create/Update for MPNS subform."""
        crypto, _created = models.BlogTag.objects.get_or_create(
            blog=blog
        )


Our Subform, repleate with asymmetric mapping and callables:

.. sourcecode::

    class BlogTagForm(forms.Form):
        """A Tag shared between blog posts that lives in another database.

        Let's pretend that this database requires RPC calls to modify any
        "model" attributes.

        """
        name = forms.CharField(
            max_length=255, required=False
        )
        author = forms.CharField(
            max_length=255, required=False
        )

        def set_author(blog_tag, author_name):
            """Set the author_name."""
            if author_name:
                blog_tag.set_author_name(author_name)

        def set_tag_name(blog_tag, tag_name):
            """Set the tag_name."""
            blog_tag.set_tag_name(tag_name)

        form_to_model = (
            ('name', set_name),
            ('author', set_author),
        )


The abriged view in which these data are saved:

.. sourcecode::

    def edit_blog_with_tags(request, blog_post):
        """Edit an application's Service Settings."""
        blog = Blog.objects.select_related().get(pk=blog_post.pk)
        mapr = mapper.Mapper(BlogForm)
        initial = mapr.get_form_data(blog)
        form = form_class(app, initial=initial)
        if request.method == 'POST':
            form = form_class(
                app,
                data=request.POST,
                files=request.FILES,
            )
            if form.is_valid():
                conf_forms = dict(form.subform_instances)
                model_instances = mapr.apply_form_data(form.cleaned_data, app)
                for model_instance in model_instances:
                    model_instance.save()

                # We successfully POST'ed, let's reload page.
                return http.HttpResponseRedirect(
                    urlresolvers.reverse(
                        'blog_detail_view', args=[blog.pk]
                    )
                )

        return direct_to_template(
            request,
            'blog/edit.html', {
                'form': form,
                'blog': blog,
            }
        )


Hierarchical Forms
==================


Purpose
^^^^^^^

There's really no good reason that I can think of for needing this
solution. At UA we found our selves in a situation in which the
configuration of multiple services depended on single form fields. The
best way to solve that problem is just to not store configuration data
that way. Due the to the way our system evolved organically, and our
sunsetting schedules, it was deemed not worth the effort to change how
these values were saved. Instead we implemented this idea of
hierarchical forms which has a major advantage in that it allows you to
inspect all of the data between subforms before concluding that the set
of forms is valid in its entirety.

.. warning:: Unless you know what you're doing, don't use hierarchical
    forms.

.. warning:: Form mapper is required for use with hierarchical forms.


Simple Example
^^^^^^^^^^^^^^

The basic usecase is to crosscheck data between some subset of subforms.
Here, the ``crosscheck_forms`` function is just taken from our actual
``ApplicationSettingsForm``, since it'd be hard to contrive something
equally well.

.. sourcecode::

    class ParentForm(HierarchicalFormBase):

        def is_valid(self):
            is_valid = super(ParentForm, self).is_valid() # calls all subforms' is_valid()
            if not is_valid:
                return false

            form_results = {}
            for attr, form in self.subform_instances:
                if self.cleaned_data.get(attr)
                    if not form.is_valid()
                        return False

                    form_results[attr] = form

            self.form_results = form_results

            return self.crosscheck_forms(self.form_results)

        def crosscheck_forms(self, forms):
            """Check field values between forms on a single page."""
            has_errors = False
            error_msg = 'Android Packages names must agree!'

            datum = lambda x, y: forms[x].cleaned_data.get(y)

            # Check if multiple forms modify the same values
            blog_attributes = (
                'tag', 'author', 'body', 'title'
            )

            # Say for example we have multiple fields which modify
            # our blog's title -- we want to see if any of them are
            # different and throw an error if they are.
            blog_data = [
                (name, datum(name, 'title')) for name, form in [
                    (name, forms.get(name)) for name in blog_attributes
                        if forms.get(name)
                ]
            ]
            if len(set([data[1] for data in blog_data])) > 1:
                # If we have more than one value for android packages,
                # then we have a problem.
                for form_name, attr_value in blog_data:
                    self._create_or_append(
                        forms, form_name, 'title', error_msg
                    )
                    has_errors = True

            return not has_errors

Core Features
^^^^^^^^^^^^^

Subform config
""""""""""""""

At UA, the ``subform_config`` is provided at runtime by the view based on circumstances.
From a parent form's ``subform_config`` it creates a list of subform_instances which contain
state for the form fields they define.

See the documentation on how the ``subform_configs`` module works.

If you're hardcoding your ``subform_config``, then the format is as follows:

.. sourcecode::

    self.subform_config = (
        ('form1_prefix', forms.Subform1),
        ('form2_prefix', forms.Subform2),
    )


.. warning:: The prefix in the subform_config must match the prefix in the form class definition!


Boolean Fields
""""""""""""""

To aide validation, we only validate those subforms which have had a boolean field
toggled to true in the parent form. Typically this is done using javascript
triggering on the .onChange() event emitter for any of the inputs within a subform.


``is_valid()``
""""""""""""""

By default, the HierarchicalFormBase (which your parent form inherits from) will call
the ``is_valid()`` function on each of the subforms that have been toggled as _modified_
on the parent form. You can then call out to things like a custom cross-form checker
(like we do in the example above) to double check that there aren't conflicts.


Testing
=======

The tests are pretty simple and don't rely on any external services. You
shouldn't have any issues firing off the tests with this commandline.

.. sourcecode:
    python setup.py develop
    python -m unittest discover


