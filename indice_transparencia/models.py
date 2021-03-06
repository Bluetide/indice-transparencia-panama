from django.db import models
from autoslug import AutoSlugField
import uuid
from templated_email import send_templated_mail
from django.contrib.sites.models import Site
from django.conf import settings
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.db.models.signals import m2m_changed, pre_save
from picklefield.fields import PickledObjectField
from django.dispatch import receiver
from model_utils.fields import AutoCreatedField, AutoLastModifiedField

class Party(models.Model):
    name = models.CharField(max_length=255, verbose_name=u"Nombre")
    initials = models.CharField(max_length=255, verbose_name=u"Iniciales")
    slug = AutoSlugField(populate_from='name', null=True)
    image = models.ImageField(verbose_name=u"Logo del partido", upload_to='party_logos/%Y/%m/%d/',
                                     null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Partido"

class Circuit(models.Model):
    name = models.CharField(max_length=255, verbose_name=u"Nombre", null=True)
    province = models.CharField(max_length=255, verbose_name=u"Provincia", default="", null=True, blank=True)
    district = models.CharField(max_length=255, verbose_name=u"Distritos", default="", null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Circuito"

class Topic(models.Model):
    name = models.CharField(max_length=255, verbose_name=u"Nombre", null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Tema Prioritario"


class EducationalRecord(models.Model):
    name = models.CharField(max_length=255, verbose_name=u"Nombre Programa")
    institution = models.CharField(max_length=255, verbose_name=u"Institución")
    start = models.CharField(max_length=255, verbose_name=u"Fecha de ingreso")
    end = models.CharField(max_length=255, verbose_name=u"Fecha de término")
    person = models.ForeignKey('Person', on_delete=models.CASCADE, related_name="educational_records", null=True)

## p = Person.objects.create(name='fiera')
## p.educational_records.all()

class WorkRecord(models.Model):
    name = models.CharField(max_length=255, verbose_name=u"Cargo")
    institution = models.CharField(max_length=255, verbose_name=u"Institución")
    start = models.CharField(max_length=255, verbose_name=u"Fecha de ingreso")
    end = models.CharField(max_length=255, verbose_name=u"Fecha de término")
    person = models.ForeignKey('Person', on_delete=models.CASCADE, related_name="work_records", null=True)


class JudiciaryProcessRecord(models.Model):
    number = models.CharField(max_length=255, verbose_name=u"Número")
    date = models.DateField(max_length=255, verbose_name=u"Fecha")
    kind = models.CharField(max_length=255, verbose_name=u"Tipo")
    result = models.TextField(max_length=255, verbose_name=u"Fallo")
    person = models.ForeignKey('Person', on_delete=models.CASCADE, related_name="judiciary_records", null=True)



class Benefit(models.Model):
    name = models.CharField(max_length=255, verbose_name='Nombre del beneficio')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Beneficio"
        
class RankingData(models.Model):
    ranking_mark = models.FloatField(null=True, blank=True)
    position_in_ranking = models.IntegerField(null=True, blank=True, default=None)

    def save(self, *args, **kwargs):
        super(RankingData, self).save(*args, **kwargs)
        

class RankingManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        return sorted(qs.all(),  key=lambda m: m.ranking_data.position_in_ranking, reverse=False)

TYPES_OF_PERSON = (('parlamentario', 'Parlamentario'), ('candidato', 'Candidato'), )


class Person(models.Model):
    #datos personales
    name = models.CharField(max_length=255, verbose_name=u"Nombre Completo")
    birth_date = models.DateField(verbose_name=u"Fecha de nacimiento.(Formato DD/MM/YYYY)", null=True, blank=True)
    email = models.EmailField(verbose_name=u"Correo electrónico de contacto", null=True, blank=True)
    web = models.URLField(max_length=512, verbose_name=u"Link al sitio web personal (o cuenta oficial en redes sociales)", null=True, blank=True)
    twitter = models.URLField(max_length=255, verbose_name=u"Cuenta de twitter", null=True, blank=True)
    instagram = models.URLField(max_length=255, verbose_name=u"Cuenta de instagram", null=True, blank=True)
    facebook = models.URLField(max_length=255, verbose_name=u"Cuenta de facebook", null=True, blank=True)
    image = models.ImageField(verbose_name=u"Foto", upload_to='profile_images/%Y/%m/%d/',
                                     null=True, blank=True)

    #perfil político
    declared_intention_to_transparent_political_profile = models.BooleanField(default=False, verbose_name=u"¿Desea Ud. compartir información sobre sus afiliaciones políticas?(Si Ud. no marca esta casilla, la información que ingrese no se visualizará ni será contabilizada en el cálculo del porcentaje)", blank=True)
    party = models.ForeignKey(Party, null=True, on_delete=models.SET_NULL, related_name="persons", blank=True, verbose_name=u"Partido político o movimiento al que representa")
    circuit = models.ForeignKey(Circuit, null=True, on_delete=models.SET_NULL, related_name="persons", blank=True, verbose_name=u"Circuito al que representa o busca representar")
    has_changed_party = models.BooleanField(default=False, verbose_name=u"¿Ha pertenecido ud. a otros partidos o movimientos políticos?", blank=True)
    previous_parties = models.ManyToManyField(Party, related_name="ex_members", verbose_name=u"Si respondió \"sí\", seleccione a qué otros partidos ha pertenecido en el pasado. Mantener “Control” o “Command” (en Mac) para seleccionar más de una opción.", blank=True)
    topics = models.ManyToManyField(Topic, related_name="person_set", blank=True, verbose_name="Por favor indique los tres temas o problemáticas en las que le gustaría enfocarse durante su gestión (2019-2024). Mantener “Control” o “Command” (en Mac) para seleccionar más de una opción.")
    other_topic = models.CharField(max_length=255, verbose_name=u"Otro tema prioritario", blank=True, null=True)

    #formación académica
    declared_intention_to_transparent_education = models.BooleanField(default=False, verbose_name=u"¿Desea Ud. compartir información sobre su formación/educación?(Si Ud. no marca esta casilla, la información que ingrese no se visualizará ni será contabilizada en el cálculo del porcentaje)", blank=True)
    extra_education = models.TextField(max_length=1024,
                                       null=True,
                                       verbose_name=u"¿Desea compartir alguna otra experiencia relevante de formación? Puede escribirlas a continuación:", blank=True)



    #experiencia_profesional
    declared_intention_to_transparent_work = models.BooleanField(default=False, verbose_name=u"¿Desea Ud. compartir información sobre su experiencia laboral?(Si Ud. no marca esta casilla, la información que ingrese no se visualizará ni será contabilizada en el cálculo del porcentaje)", blank=True)



    #propuesta política
    declared_intention_to_transparent_political_proposal = models.BooleanField(default=False, verbose_name=u"¿Desea Ud. compartir su propuesta política de diputado(a) o candidato(a)?(Si Ud. no marca esta casilla, la información que ingrese no se visualizará ni será contabilizada en el cálculo del porcentaje)", blank=True)
    has_political_proposal = models.BooleanField(default=False, verbose_name=u"Ya sea diputado(a) o candidato(a), ¿Cuenta ud. con una propuesta política para su gestión (2019-2024)?", blank=True)
    political_proposal_link = models.URLField(null=True, max_length=255, verbose_name=u"Si respondió \"sí\", indique en qué link se puede acceder a su propuesta política", blank=True)
    political_proposal_doc = models.FileField(upload_to='political_proposals/%Y/%m/%d/',
                                     null=True,
                                     verbose_name=u"", blank=True)


    #delaracion de patrimonio e intereses
    intention_to_transparent_patrimony = models.BooleanField(default=False, verbose_name=u"¿Desea Ud. compartir sus declaraciones de Patrimonio e Intereses?(Si Ud. no marca esta casilla, la información que ingrese no se visualizará ni será contabilizada en el cálculo del porcentaje)", blank=True)
    existing_patrimony_declaration = models.BooleanField(default=False, null=True, verbose_name=u"¿Cuenta ud. con una declaración de patrimonio actualizada?", blank=True)
    patrimony_link = models.URLField(null=True,
                                     verbose_name=u"Si respondió 'sí' por favor indique a continuación el link para acceder a su declaración de patrimonio", blank=True)
    patrimony_doc = models.FileField(upload_to='patrimony/%Y/%m/%d/',
                                     null=True,
                                     verbose_name=u"", blank=True)
    existing_interests_declaration = models.BooleanField(default=False, null=True, verbose_name=u"¿Cuenta ud. con una declaración de intereses actualizada?", blank=True)
    interests_link = models.CharField(max_length=255, null=True,
                                      verbose_name=u"Si respondió 'sí' por favor indique a continuación el link para acceder a su declaración de Intereses", blank=True)
    interests_doc = models.FileField(upload_to='interests/%Y/%m/%d/',
                                     null=True,
                                     verbose_name=u"", blank=True)


    #procesos judiciales
    declared_intention_to_transparent_judiciary_records = models.BooleanField(default=False,
                                                verbose_name=u"¿Desea Ud. compartir información sobre los procesos judiciales en los que ha estado involucrado(a)?(Si Ud. no marca esta casilla, la información que ingrese no se visualizará ni será contabilizada en el cálculo del porcentaje)", blank=True)
    judiciary_processes_involved = models.IntegerField(null=True, blank=True, verbose_name=u"¿En cuántos procesos judiciales ud. se ha visto involucrado en los últimos 10 años?")
    extra_judiciary_declaration = models.TextField(max_length=255,null=True, verbose_name=u"¿Se ha visto involucrado en más procesos judiciales en los últimos 10 años?", blank=True)
    judiciary_link = models.URLField(null=True, verbose_name=u"Si respondió 'sí', por favor indique dónde se puede acceder a esta información (facilite un link u otro recurso)", blank=True)
    judiciary_description = models.TextField(null=True, verbose_name=u"¿Desea agregar comentarios o notas aclaratorias sobre uno o más de los procesos judiciales declarados? Puede hacerlo a continuación", blank=True)


    #etica presupuestaria
    is_deputy = models.BooleanField(default=False, null=True, blank=True, verbose_name=u"¿Eres actualmente diputado/a?")
    declared_intention_to_transparent_public_resources_usage = models.BooleanField(default=False, verbose_name=u"¿Desea Ud. compartir información sobre su uso de recursos públicos?(Si Ud. no marca esta casilla, la información que ingrese no se visualizará ni será contabilizada en el cálculo del porcentaje)", blank=True)
    benefits = models.ManyToManyField(Benefit, blank=True)
    benefits_link = models.CharField(max_length=512,
                                     verbose_name=u"Por favor, indique en qué link es posible acceder al detalle sobre los montos asociados a su uso de beneficios",
                                     null=True, blank=True)
    benefits_doc = models.FileField(upload_to='benefits/%Y/%m/%d/',
                                     null=True,
                                     verbose_name=u"", blank=True)

    # declared_intention_to_transparent = models.BooleanField(default=False, verbose_name=u"¿Desea Ud. transparentar su información política general?", blank=True)
    # period = models.CharField(max_length=255, verbose_name=u"¿En qué período legislativo se encuentra actualmente?", null=True, blank=True)

    # reelection = models.BooleanField(default=False, verbose_name=u"¿Va a reelección?", null=True, blank=True)

    # intention_to_transparent_work_plan = models.BooleanField(default=False, verbose_name=u"¿Desea Ud. transparentar su plan de trabajo de diputado(a) o candidato(a)?", blank=True)

    # work_plan_link = models.URLField(null=True, max_length=255, verbose_name=u"Si respondió 'sí', indique en qué link se puede acceder a su programa de trabajo", blank=True)
    # work_plan_doc = models.FileField(upload_to='work_plans/%Y/%m/%d/',
    #                                  null=True,
    #                                  verbose_name=u"Si respondió 'sí' pero no tiene su plan de trabajo online, acá tiene la posibilidad de adjuntar el archivo", blank=True)
    eth_001_link = models.URLField(verbose_name=u"Indique en qué link es posible acceder al detalle de su planilla 001",
                                    null=True, blank=True)
    eth_001_doc = models.FileField(upload_to='eth_001/%Y/%m/%d/', null=True, blank=True,
                                    verbose_name=u"")
    eth_002_link = models.URLField(verbose_name=u"Indique en qué link es posible acceder al detalle de su planilla 002",
                                    null=True, blank=True)
    eth_002_doc = models.FileField(upload_to='eth_002/%Y/%m/%d/', null=True, blank=True,
                                    verbose_name=u"")
    eth_080_link = models.URLField(verbose_name=u"Indique en qué link es posible acceder al detalle de su planilla 080",
                                   null=True, blank=True)
    eth_080_doc = models.FileField(upload_to='eth_080/%Y/%m/%d/',
                                  verbose_name=u"",
                                   null=True, blank=True)
    eth_172_link = models.URLField(verbose_name=u"Indique en qué link es posible acceder al detalle de su planilla 172",
                                   null=True, blank=True)
    eth_172_doc = models.FileField(upload_to='eth_172/%Y/%m/%d/',
                                  verbose_name=u"",
                                   null=True, blank=True)

    attendance = models.FloatField(verbose_name="Indique su porcentaje de asistencia a la Asamblea Nacional durante este período legislativo", null=True, blank=True)
    laws_worked_on = models.IntegerField(verbose_name="Indique el número de leyes que ud. ha sancionado en el último período legislativo", null=True, blank=True)

    ranking_mark = models.IntegerField(null=True, blank=True)
    position_in_ranking = models.IntegerField(null=True, blank=True, default=None)
    
    ranking_data = models.OneToOneField(RankingData, null=True, on_delete=models.CASCADE, related_name="person", blank=True, verbose_name=u"")

    slug = AutoSlugField(populate_from='name', null=True)
    volunteer_changed = PickledObjectField(default=list)
    
    created = AutoCreatedField()
    modified = AutoLastModifiedField()
    
    objects = models.Manager() # The default manager.
    ranking = RankingManager() # The Dahl-specific manager.

    def get_mark(self):
        final_mark = 0
        if self.educational_records.exists():
            final_mark += 0.5
        if self.work_records.exists():
            final_mark += 0.5
        # if self.patrimony_link or self.patrimony_doc:
        #     if 'patrimony' in self.volunteer_changed:
        #         final_mark += 1
        #     else:
        #         final_mark += 1
        # if self.interests_link or self.interests_doc:
        #     if 'interests' in self.volunteer_changed:
        #         final_mark += 1
        #     else:
        #         final_mark += 1
        if self.is_deputy:
            if self.patrimony_link or self.patrimony_doc:
                if 'patrimony' in self.volunteer_changed:
                    final_mark += 1
                else:
                    final_mark += 1
            if self.interests_link or self.interests_doc:
                if 'interests' in self.volunteer_changed:
                    final_mark += 1
                else:
                    final_mark += 1
            if self.declared_intention_to_transparent_judiciary_records:
                if 'declared_intention_to_transparent_judiciary_records' in self.volunteer_changed:
                    final_mark += 2
                else:
                    final_mark += 2
            if self.political_proposal_link or self.political_proposal_doc:
                # volunteer_changed_politcal_proposal = 'political_proposal_link' in self.volunteer_changed or 'political_proposal_doc' in self.volunteer_changed
                final_mark += 2
            if self.benefits_link or self.benefits_doc:
                if 'benefits' in self.volunteer_changed:
                    final_mark += 0.5
                else:
                    final_mark += 0.5
            if self.eth_001_link or self.eth_001_doc:
                if 'eth_001' in self.volunteer_changed:
                    final_mark += 0.25
                else:
                    final_mark += 0.25
            if self.eth_002_link or self.eth_002_doc:
                if 'eth_002' in self.volunteer_changed:
                    final_mark += 0.25
                else:
                    final_mark += 0.25
            if self.eth_080_link or self.eth_080_doc:
                if 'eth_080' in self.volunteer_changed:
                    final_mark += 0.25
                else:
                    final_mark += 0.25
            if self.eth_172_link or self.eth_172_doc:
                if 'eth_172' in self.volunteer_changed:
                    final_mark += 0.25
                else:
                    final_mark += 0.25
        else:
            if self.patrimony_link or self.patrimony_doc:
                if 'patrimony' in self.volunteer_changed:
                    final_mark += 1.75
                else:
                    final_mark += 1.75
            if self.interests_link or self.interests_doc:
                if 'interests' in self.volunteer_changed:
                    final_mark += 1.75
                else:
                    final_mark += 1.75
            if self.political_proposal_link or self.political_proposal_doc:
                final_mark += 2
            if self.declared_intention_to_transparent_judiciary_records:
                if 'declared_intention_to_transparent_judiciar75y_records' in self.volunteer_changed:
                    final_mark += 2
                else:
                    final_mark += 2
        tmp = 100*(final_mark / 8.5)
        
        final_mark = round(tmp,1)

        return final_mark

    def update_mark(self):
        self.ranking_data.ranking_mark = self.get_mark()
        self.ranking_data.save()

    def get_absolute_url(self):
        return reverse('candidate-profile', kwargs={'slug': self.slug})

    def __str__(self):
        return self.name
        
    def save(self, *args, **kwargs):
        creating = False
        if self.id is None:
            creating = True    
        if creating:
            ranking_data = RankingData.objects.create(person=self)
            self.ranking_data = ranking_data
       
        # ranking_data = RankingData.objects.get_or_create(person=self)
        # self.ranking_data = ranking_data[0]
        super(Person, self).save(*args, **kwargs)
        self.update_mark()
        update_positions_in_ranking()

    class Meta:
        verbose_name = "Persona"

def topics_changed(sender, **kwargs):
    if kwargs['instance'].topics.count() > 3:
        raise ValidationError({'topics': "You can't assign more than three topics"})

m2m_changed.connect(topics_changed, sender=Person.topics.through)



class Contact(models.Model):
    person = models.ForeignKey(Person, related_name='contact', on_delete=models.CASCADE)
    email = models.EmailField(max_length=255)
    identifier = models.UUIDField(default=uuid.uuid4, editable=False)

    def save(self, *args, **kwargs):
        creating = False
        if self.id is None:
            creating = True
        super(Contact, self).save(*args, **kwargs)
        if creating:
            site = Site.objects.get_current()
            send_templated_mail(
                                template_name=settings.TEMPLATE_TO_USE_WHEN_SENDING_EMAIL,
                                from_email=settings.DEFAULT_FROM_EMAIL,
                                recipient_list=[self.email],
                                context={
                                    'contact': self,
                                    'person': self.person,
                                    'site': site,
                                },
                        )
            self.person.email = self.email
            self.person.save()

    def update_url(self):
        return reverse('update-person-data', kwargs={'identifier': self.identifier})

    class Meta:
        verbose_name = "Contacto"



def update_positions_in_ranking():
    ## Aquí hago la wea J!
        
    counter = 1
    for p in Person.objects.all().order_by('-ranking_data__ranking_mark','name'):
        p.ranking_data.position_in_ranking = counter
        p.ranking_data.save()
        counter += 1


def update_mark_and_position_in_ranking(person):
    person.update_mark()
    update_positions_in_ranking()
