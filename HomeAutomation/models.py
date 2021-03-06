from django.db import models
from HomeAutomation.SSHConnection import Connection
from HomeAutomation.validators import VariableValidations
from HomeAutomation.exceptions import *
import requests
import time
import sys


class Parameters(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True, null=False)
    value = models.CharField(max_length=100, unique=True, null=False)

    def __str__(self):
        return self.name

    def get_change_v_method(self):
        reg = self.objects.filter(name="changeVariable").first()
        return reg.value

    def get_script_name(self):
        reg = self.objects.filter(name="script").first()
        return reg.value


class ArtifactType(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True, null=False)

    class Meta:
        verbose_name = 'Tipo de Artefacto'
        verbose_name_plural = 'Tipos de Artefactos'

    def __str__(self):
        return self.name

    # def __eq__(self, other):
    #   return self.name == other.name


class SSHConfig(models.Model):
    id = models.AutoField(primary_key=True)
    artifactType = models.OneToOneField(ArtifactType, on_delete=models.DO_NOTHING, blank=False, null=False)
    script = models.CharField(max_length=100, null=False)
    method = models.CharField(max_length=100, null=False)

    class Meta:
        verbose_name = 'Configuracion de SSH'
        verbose_name_plural = 'Configuraciones de SSH'

    def __str__(self):
        return self.script + ' - ' + self.method


class WSConfig(models.Model):
    id = models.AutoField(primary_key=True)
    artifactType = models.OneToOneField(ArtifactType, on_delete=models.DO_NOTHING, blank=False, null=False)
    name = models.CharField(max_length=100, null=False)

    class Meta:
        verbose_name = 'Configuracion de WS'
        verbose_name_plural = 'Configuraciones de WS'

    def __str__(self):
        return self.name


class Intermediary(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=40, unique=True, null=False)
    user = models.CharField(max_length=40, unique=False, null=False)
    password = models.CharField(max_length=40, unique=False, null=False)

    class Meta:
        verbose_name = 'Actuador'
        verbose_name_plural = 'Actuadores'

    def __str__(self):
        return self.name


class Zone(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True, null=False)
    type = models.CharField(max_length=40, unique=False, null=True, blank=True)
    pin = models.IntegerField(null=True, blank=True)
    intermediary = models.ForeignKey(Intermediary, on_delete=models.DO_NOTHING, blank=True, null=True)
    temperature = models.FloatField(null=True, blank=True)

    class Meta:
        verbose_name = 'Zona'
        verbose_name_plural = 'Zonas'

    def __str__(self):
        return self.name

    def set_temperature(self, value):
        self.temperature = value
        self.save(update_fields=['temperature'])


class Artifact(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=False, null=False)
    type = models.ForeignKey(ArtifactType, on_delete=models.DO_NOTHING)
    zone = models.ForeignKey(Zone, on_delete=models.DO_NOTHING, null=True)
    intermediary = models.ForeignKey(Intermediary, on_delete=models.DO_NOTHING, null=True)
    on = models.BooleanField(default=False)
    connector = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        verbose_name = 'Artefacto'
        verbose_name_plural = 'Artefactos'

    def __str__(self):
        return self.name + " (" + self.zone.name + ")"

    def change_power(self, power):
        self.on = power
        # params = Parameters()
        # method_name = params.get_change_v_method()
        ssh = SSHConfig.objects.filter(artifactType=self.type.id).first()
        if ssh:
            command = ssh.method + "(" + str(self.connector) + ", " + power + ")"
            print(command, self.intermediary.name, self.intermediary.user, self.intermediary.password, ssh.script)
            try:
                Connection.execute_script(self.intermediary.name, self.intermediary.user, self.intermediary.password, ssh.script, command)
            except:
                print(sys.exc_info())
                raise ConnectionExc()
            self.save(update_fields=['on'])
            return True
        ws = WSConfig.objects.filter(artifactType=self.type.id).first()
        if ws:
            url = 'http://' + self.intermediary.name + '/' + ws.name
            print(url)
            if self.type.name == 'AC' and power == '1':
                variables = StateVariable.objects.filter(artifact=self.id)
                code = ''
                for v in variables:
                    print(v)
                    code += '#' + v.value if len(code) > 0 else v.value
                print(code)
            else:
                code = '0'
            # cuando no es un AC, o es un off que se manda un cero:
            try:
                art_code = ArtifactCode.objects.filter(code=code).first()
                raw_code = art_code.raw
                code_array = VariableValidations.parse_raw_to_array(raw_code)
                req = requests.put(url, json={'value': code_array})
                print(req.text)
            except:
                raise ConnectionExc()
            self.save(update_fields=['on'])
            return True
            # consumir ws.. etc
        raise ConfigurationExc()

    def is_on(self):
        return self.on


class VariableType(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True, null=False)

    class Meta:
        verbose_name = 'Tipo de Variable'
        verbose_name_plural = 'Tipos de Variables'

    def __str__(self):
        return self.name


class StateVariable(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=False, null=False)
    artifact = models.ForeignKey(Artifact, on_delete=models.DO_NOTHING, related_name='variables')
    type = models.ForeignKey(VariableType, on_delete=models.DO_NOTHING, null=True)
    value = models.CharField(max_length=50, null=True)
    min = models.IntegerField(default=0)
    max = models.IntegerField(default=1)
    scale = models.IntegerField(default=1)

    class Meta:
        verbose_name = 'Variable de Estado'
        verbose_name_plural = 'Variables de Estado'

    def __str__(self):
        return self.id + ' - ' + self.name

    def change_variable(self, value):
        # a = Artifact.objects.filter(id=self.artifact).first()
        value = int(value)
        validator = VariableValidations()
        try:
            validator.value_validation(self,  value)
        except:
            raise ValidationExc()

        self.value = value
        ssh = SSHConfig.objects.filter(artifactType=self.artifact.type.id).first()
        if ssh:
            command = ssh.method + "(" + str(self.artifact.connector) + "," + value + ")"
            try:
                Connection.execute_script(self.artifact.intermediary.name, self.artifact.intermediary.user,
                                          self.artifact.intermediary.password, ssh.script, command)
            except:
                raise ConnectionExc()
            self.save(update_fields=['value'])
            return True

        ws = WSConfig.objects.filter(artifactType=self.artifact.type.id).first()
        if ws:
            url = 'http://' + self.artifact.intermediary.name + '/' + ws.name
            code = value
            print(url)
            if self.artifact.type.name == 'AC':
                variables = StateVariable.objects.filter(artifact=self.artifact.id)
                code = ''
                for v in variables:
                    print(v)
                    if v.id == self.id:
                        code += '#' + str(value) if len(code) > 0 else str(value)
                    else:
                        code += '#' + str(v.value) if len(code) > 0 else str(v.value)
                print(code)
                try:
                    art_code = ArtifactCode.objects.filter(code=code).first()
                    raw_code = art_code.raw
                    code_array = validator.parse_raw_to_array(raw_code)
                    req = requests.put(url, json={'value': code_array})
                    print(req.text)
                except:
                    raise ConnectionExc()
            self.save(update_fields=['value'])
            return True
        raise ConfigurationExc()


class VariableRange(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=False, null=False)
    type = models.CharField(max_length=50, null=True)
    value = models.CharField(max_length=50, default=0, null=False)
    variable = models.ForeignKey(StateVariable, on_delete=models.DO_NOTHING, null=False, related_name='ranges')

    class Meta:
        verbose_name = 'Rango de Variable'
        verbose_name_plural = 'Rangos de Variables'

    def __str__(self):
        return self.name + ' ( ' + self.variable.artifact.name + '-' + self.variable + ')'


class Role(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=False, null=False)

    def __str__(self):
        return self.name


class User(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True, null=False)
    question = models.CharField(max_length=100, unique=False, null=True)
    answer = models.CharField(max_length=100, unique=False, null=True)
    password = models.CharField(max_length=100, unique=False, null=False)
    isAdmin = models.BooleanField(null=False, default=False)

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def verify_old_password(self, old_password):
        return old_password == self.password

    def login(self, password):
        return self.password == password

    def check_answer(self, answer):
        return self.answer == answer

    def is_admin(self):
        return self.isAdmin

    def get_question(self):
        return self.question

    def get_question(self):
        return self.question

    def change_password(self, new_password):
        self.password = new_password
        return True

    def __str__(self):
        return self.name


class Scene(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True, null=False)
    description = models.CharField(max_length=200, null=False)
    on_demand = models.BooleanField(default=False)
    time_condition = models.BooleanField(default=False)
    time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    days = models.CharField(max_length=20, blank=True, null=True)
    value_condition = models.BooleanField(default=False)
    value = models.CharField(max_length=30, null=True, blank=True)
    condition_operation = models.CharField(max_length=20, null=True, blank=True)
    zone = models.ForeignKey(Zone, on_delete=models.DO_NOTHING, null=True, blank=True)
    executed = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Escena'
        verbose_name_plural = 'Escenas'

    def __str__(self):
        return self.name

    def execute_scene(self):
        actions = SceneAction.objects.filter(scene=self.id).all()
        for action in actions:
            value = action.value
            if action.variable == 0:
                action.artifact.change_power(value)
            else:
                action.variable.change_variable(value)
            time.sleep(1)
        if self.value_condition:
            self.change_executed(True)
        return True

    def change_executed(self, bool):
        self.executed = bool
        self.save(update_fields=['executed'])


class SceneAction(models.Model):
    id = models.AutoField(primary_key=True)
    zone = models.ForeignKey(Zone, on_delete=models.DO_NOTHING)
    artifact = models.ForeignKey(Artifact, on_delete=models.DO_NOTHING)
    variable = models.IntegerField(default=0)
    value = models.CharField(max_length=50, null=False)
    scene = models.ForeignKey(Scene, on_delete=models.DO_NOTHING, related_name='actions')

    class Meta:
        verbose_name = 'Accion'
        verbose_name_plural = 'Acciones de Escenas'

    def __str__(self):
        return self.scene.name + ' - ' + self.artifact.name


class ArtifactCode(models.Model):
    id = models.AutoField(primary_key=True)
    artifact = models.ForeignKey(Artifact, on_delete=models.DO_NOTHING, null=False)
    code = models.CharField(max_length=20, null=False)
    hexa = models.CharField(max_length=20, null=True, blank=True)
    raw = models.CharField(max_length=4000, null=True, blank=True)

    class Meta:
        verbose_name = 'Codigos de Artefacto'
        verbose_name_plural = 'Codigos de Artefactos'

    def __str__(self):
        return self.code
