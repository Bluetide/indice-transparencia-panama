from django.test import TestCase
from indice_transparencia.models import Person, Party, Contact
from indice_transparencia.forms import PersonForm
from django.urls import reverse



class PersonUpdateView(TestCase):
    def test_get_the_view(self):
        p = Person.objects.create(name=u'Fiera',
                                  specific_type='parlamentario')
        contact = Contact.objects.create(person=p, email='jordi@cidadaniai.org')
        url = reverse('update-person-data', kwargs={'identifier': contact.identifier})
        response = self.client.get(url)
        form = response.context['form']
        assert form.instance == p
        assert isinstance(form, PersonForm)

    def test_post_to_the_view(self):
        partido = Party.objects.create(name=u'Partido Feroz',
                                       initials='PF')
        p = Person.objects.create(name=u'Fiera',
                                  specific_type='parlamentario')
        contact = Contact.objects.create(person=p, email='jordi@cidadaniai.org')
        url = reverse('update-person-data', kwargs={'identifier': contact.identifier})
        data = {
            'birth_date': '01/31/1980',
            'web': 'https://jordipresidente.pa',
            'declared_intention_to_transparent': True,
            'party': partido.id,
            'circuit': 'Panama',
            'period': '2018',
            'previous_parties': [],
            'reelection': True,
            'extra_education': 'Me gusta educarme',
            'intention_to_transparent_work_plan': True,
            'work_plan_link': 'https://jordipresidente.pa/transparencia',
            'work_plan_doc': None,
            'intention_to_transparent_patrimony': True,
            'patrimony_link': 'https://jordipresidente.pa/transparencia',
            'patrimony_doc': None,
            'existing_interests_declaration': True,
            'interests_link': 'https://jordipresidente.pa/transparencia',
            'interests_doc': None,
            'judiciary_declaration': True,
            'extra_judiciary_declaration': 'No tengo nada!!!',
            'judiciary_link': 'https://jordipresidente.pa/transparencia',
            'judiciary_description': 'Judiciary',
            'benefits': [],
            'benefits_link': 'https://jordipresidente.pa/transparencia',
            'eth_080_link': 'https://jordipresidente.pa/transparencia',
            'eth_172_link': 'https://jordipresidente.pa/transparencia',
            'eth_080_doc': None,
            'eth_172_doc': None
        }
        response = self.client.post(url, data=data)
        assert response.status_code == 200
        p.refresh_from_db()
        #Soy un flojo y revisaré una sola cosa
        assert p.web
