from django.conf import settings
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import IntegrityError

from elections.models import Election, BackgroundCategory, Background, BackgroundCandidate, Candidate
from elections.forms import BackgroundForm


class BackgroundModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='joe', password='doe', email='joe@doe.cl')
        self.election, created = Election.objects.get_or_create(name='BarBaz',
                                                            owner=self.user,
                                                            slug='barbaz')
        self.background_category, created = BackgroundCategory.objects.get_or_create(election=self.election,
                                                                    name='FooBar')

    def test_create_background(self):
        background, created = Background.objects.get_or_create(category=self.background_category,
                                                                name='foo')
        self.assertTrue(created)
        self.assertEqual(background.name, 'foo')
        self.assertEqual(background.category, self.background_category)


class BackgroundCreateView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='joe', password='doe', email='joe@doe.cl')
        self.election, created = Election.objects.get_or_create(name='BarBaz',
                                                            owner=self.user,
                                                            slug='barbaz')
        self.background_category, created = BackgroundCategory.objects.get_or_create(election=self.election,
                                                                    name='FooBar')

    def test_create_background_by_user_without_login(self):
        request = self.client.get(reverse('background_create',
                                    kwargs={'background_category_pk': self.background_category.pk}))
        self.assertEquals(request.status_code, 302)

    def test_create_background_by_user_success(self):
        self.client.login(username='joe', password='doe')
        request = self.client.get(reverse('background_create',
                                    kwargs={'background_category_pk': self.background_category.pk}))

        self.assertEqual(request.status_code, 200)
        self.assertTrue('form' in request.context)
        self.assertTrue(isinstance(request.context['form'], BackgroundForm))
        self.assertTrue('background_category' in request.context)
        self.assertTrue(isinstance(request.context['background_category'], BackgroundCategory))

    def test_post_background_create_without_login(self):
        params = {'name': 'Bar'}
        response = self.client.post(reverse('background_create',
                                        kwargs={'background_category_pk': self.background_category.pk}),
                                    params)

        self.assertEquals(response.status_code, 302)

    def test_get_background_create_with_login_stranger_background_category(self):
        self.client.login(username='joe', password='doe')
        response = self.client.get(reverse('background_create',
                                    kwargs={'background_category_pk': 97965678765}))
        self.assertEquals(response.status_code, 404)

    def test_post_background_create_with_login_stranger_background_category(self):
        self.client.login(username='joe', password='doe')

        params = {'name': 'Bar'}
        response = self.client.post(reverse('background_create',
                                        kwargs={'background_category_pk': 23678543567}),
                                    params)
        self.assertEquals(response.status_code, 404)

    def test_post_background_create_logged(self):
        self.client.login(username='joe', password='doe')

        params = {'name': 'Bar'}
        response = self.client.post(reverse('background_create',
                                        kwargs={'background_category_pk': self.background_category.pk}),
                                    params,
                                    follow=True)

        self.assertEquals(response.status_code, 200)
        qs = Background.objects.filter(name='Bar')
        self.assertEquals(qs.count(), 1)
        background = qs.get()
        self.assertEqual(background.name, params['name'])
        self.assertEqual(background.category, self.background_category)

        self.assertRedirects(response, reverse('background_category_create',
                                               kwargs={'election_slug': self.election.slug}))


class BackgroundCandidateModelTest(TestCase):
    def test_background_candidate_create(self):
        self.user = User.objects.create_user(username='joe', password='doe', email='joe@doe.cl')
        self.election, created = Election.objects.get_or_create(name='BarBaz',
                                                            owner=self.user,
                                                            slug='barbaz')
        self.background_category, created = BackgroundCategory.objects.get_or_create(election=self.election,
                                                                    name='FooBar')

        self.background, created = Background.objects.get_or_create(category=self.background_category,
                                                                name='foo')

        self.candidate, created = Candidate.objects.get_or_create(first_name='Juan',
                                                            last_name='Candidato',
                                                            slug='juan-candidato',
                                                            election=self.election)

        background_candidate, created = BackgroundCandidate.objects.get_or_create(candidate=self.candidate,
                                                                                       background=self.background,
                                                                                       value='new_value')

        self.assertEqual(background_candidate.candidate, self.candidate)
        self.assertEqual(background_candidate.background, self.background)
        self.assertEqual(background_candidate.value, 'new_value')


class BackgroundCandidateCreateView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='joe', password='doe', email='joe@doe.cl')
        self.election, created = Election.objects.get_or_create(name='BarBaz',
                                                            owner=self.user,
                                                            slug='barbaz')
        self.background_category, created = BackgroundCategory.objects.get_or_create(election=self.election,
                                                                    name='FooBar')

        self.background, created = Background.objects.get_or_create(category=self.background_category,
                                                                name='foo')

        self.candidate, created = Candidate.objects.get_or_create(first_name='Juan',
                                                            last_name='Candidato',
                                                            slug='juan-candidato',
                                                            election=self.election)

    def test_create_background_candidate_by_user_without_login(self):
        response = self.client.get(reverse('background_candidate_create',
                                    kwargs={'candidate_pk': self.candidate.pk,
                                            'background_pk': self.background.pk}))
        self.assertEquals(response.status_code, 302)

    def test_create_background_candidate_by_user_success(self):
        self.client.login(username='joe', password='doe')
        request = self.client.get(reverse('background_candidate_create',
                                    kwargs={'candidate_pk': self.candidate.pk,
                                            'background_pk': self.background.pk}))

        self.assertEqual(request.status_code, 200)
        self.assertTrue('form' in request.context)
        self.assertTrue(isinstance(request.context['form'], BackgroundCandidateForm))
        self.assertTrue('candidate' in request.context)
        self.assertTrue(isinstance(request.context['candidate'], Candidate))
        self.assertTrue('background' in request.context)
        self.assertTrue(isinstance(request.context['background'], Background))

    def test_post_background_candidate_create_without_login(self):
        params = {'value': 'Bar'}
        response = self.client.get(reverse('background_candidate_create',
                                    kwargs={'candidate_pk': self.candidate.pk,
                                            'background_pk': self.background.pk}),
                                    params)

        self.assertEquals(response.status_code, 302)

    def test_get_background_candidate_create_with_login_stranger_background_category(self):
        self.client.login(username='joe', password='doe')
        response = self.client.get(reverse('background_create',
                                    kwargs={'background_category_pk': 97965678765}))
        self.assertEquals(response.status_code, 404)

    def test_post_background_candidate_create_with_login_stranger_background_category(self):
        self.client.login(username='joe', password='doe')

        params = {'value': 'Bar'}
        response = self.client.get(reverse('background_candidate_create',
                                    kwargs={'candidate_pk': self.candidate.pk,
                                            'background_pk': self.background.pk}),
                                    params)
        self.assertEquals(response.status_code, 404)

    def test_post_background_create_logged(self):
        self.client.login(username='joe', password='doe')

        params = {'value': 'Bar'}
        response = self.client.get(reverse('background_candidate_create',
                                    kwargs={'candidate_pk': self.candidate.pk,
                                            'background_pk': self.background.pk}),
                                    params,
                                    follow=True)

        self.assertEquals(response.status_code, 200)
        qs = BackgroundCandidate.objects.filter(value='Bar')
        self.assertEquals(qs.count(), 1)
        background_candidate = qs.get()
        self.assertEqual(background_candidate.value, params['value'])
        self.assertEqual(background_candidate.candidate, self.candidate)
        self.assertEqual(background_candidate.background, self.background)

        self.assertRedirects(response, reverse('background_candidate_create',
                                    kwargs={'candidate_pk': self.candidate.pk,
                                            'background_pk': self.background.pk}))
