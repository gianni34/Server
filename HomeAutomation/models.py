from django.db import models
from HomeAutomation.SSHConnection import Connection
from HomeAutomation.validators import VariableValidations
import requests
import time


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

    def __str__(self):
        return self.name

    # def __eq__(self, other):
    #   return self.name == other.name


class SSHConfig(models.Model):
    id = models.AutoField(primary_key=True)
    artifactType = models.OneToOneField(ArtifactType, on_delete=models.DO_NOTHING, blank=False, null=False)
    script = models.CharField(max_length=100, null=False)
    method = models.CharField(max_length=100, null=False)

    def __str__(self):
        return self.script + ' - ' + self.method


class WSConfig(models.Model):
    id = models.AutoField(primary_key=True)
    artifactType = models.OneToOneField(ArtifactType, on_delete=models.DO_NOTHING, blank=False, null=False)
    name = models.CharField(max_length=100, null=False)

    def __str__(self):
        return self.name


class Intermediary(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=40, unique=True, null=False)
    ip = models.CharField(max_length=20, unique=True, null=False)
    user = models.CharField(max_length=40, unique=False, null=False)
    password = models.CharField(max_length=40, unique=False, null=False)

    def __str__(self):
        return self.name + ' -  IP: ' + self.ip


class Zone(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True, null=False)
    type = models.CharField(max_length=40, unique=False, null=True)
    pin = models.IntegerField(null=True)
    intermediary = models.ForeignKey(Intermediary, on_delete=models.DO_NOTHING, blank=True, null=True)
    temperature = models.FloatField(null=True)

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
    connector = models.CharField(max_length=100, null=True)

    def __str__(self):
        return self.name + "(" + self.zone.name + ")"

    def change_power(self, power):
        self.on = power
        # params = Parameters()
        # method_name = params.get_change_v_method()
        ssh = SSHConfig.objects.filter(artifactType=self.type.id).first()
        if ssh:
            on = '1' if power else '0'
            command = ssh.method + "(" + str(self.connector) + "," + on + ")"
            Connection.execute_script(intermediary.name, self.intermediary.user, self.intermediary.password, ssh.script, command)
            self.save(update_fields=['on'])
            return
        ws = WSConfig.objects.filter(artifactType=self.type.id).first()
        if ws:
            url = 'http://' + self.intermediary.name + '/' + ws.name
            print(url)
            if self.type.name == 'AC' and power:
                variables = StateVariable.objects.filter(artifact=self.id)
                code = ''
                for v in variables:
                    print(v)
                    code += '#' + v.value if len(code) > 0 else v.value
                print(code)
                req = requests.put(url, json={'value': code})
                print(req.text)
                return
            else:
                on = '1'
                if not power:
                    on = '0'
                # cuando no es un AC, o es un off que se manda un cero:
                req = requests.put(url, json={'value': on})
                print(req.text)
                return
            # consumir ws.. etc
            return

    def is_on(self):
        return self.on


class StateVariable(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=False, null=False)
    artifact = models.ForeignKey(Artifact, on_delete=models.DO_NOTHING, related_name='variables')
    type = models.CharField(max_length=50, null=True)
    typeUI = models.CharField(max_length=50, null=True)
    value = models.CharField(max_length=50, null=True)
    min = models.IntegerField(default=0)
    max = models.IntegerField(default=1)
    scale = models.IntegerField(default=1)

    def __str__(self):
        return self.name

    def change_variable(self, value):
        # a = Artifact.objects.filter(id=self.artifact).first()
        validate = VariableValidations.value_validation(self.id, value)
        if not validate.result:
            return validate

        self.value = value
        ssh = SSHConfig.objects.filter(artifactType=self.artifact.type.id).first()
        if ssh:
            command = ssh.method + "(" + str(self.artifact.connector) + "," + value + ")"
            Connection.execute_script(intermediary.name, self.artifact.intermediary.user, self.artifact.intermediary.password, ssh.script,
                                      command)
            self.save(update_fields=['value'])
            return {'result': True, 'message': 'Se modificó correctamente.'}

        ws = WSConfig.objects.filter(artifactType=self.artifact.type.id).first()
        if ws:
            url = 'http://' + self.intermediary.name + '/' + ws.name
            print(url)
            if self.artifact.type.name == 'AC':
                variables = StateVariable.objects.filter(artifact=self.artifact.id)
                code = ''
                for v in variables:
                    print(v)
                    if v.id == self.id:
                        code += '#' + value if len(code) > 0 else value
                    else:
                        code += '#' + v.value if len(code) > 0 else v.value
                print(code)
                req = requests.put(url, json={'value': code})
                print(req.text)
            else:
                req = requests.put(url, json={'value': value})
                print(req.text)
            return {'result': True, 'message': 'Se modificó correctamente.'}
        return {'result': False, 'message': 'El artefacto esta mal configurado.'}


class VariableRange(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=False, null=False)
    type = models.CharField(max_length=50, null=True)
    value = models.CharField(max_length=50, default=0, null=False)
    variable = models.ForeignKey(StateVariable, on_delete=models.DO_NOTHING, null=False, related_name='ranges')

    def __str__(self):
        return self.name


class Role(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=False, null=False)

    def __str__(self):
        return self.name


class User(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True, null=False)
    # role = models.ForeignKey(Role, on_delete=models.DO_NOTHING, null=False)
    question = models.CharField(max_length=100, unique=False, null=True)
    answer = models.CharField(max_length=100, unique=False, null=True)
    password = models.CharField(max_length=100, unique=False, null=False)
    isAdmin = models.BooleanField(null=False, default=False)

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

    def __str__(self):
        return self.name


class Scene(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True, null=False)
    description = models.CharField(max_length=200, unique=False, null=False)
    end_time = models.DateTimeField(null=True)
    initial_time = models.DateTimeField(null=True)
    frequency = models.CharField(max_length=20, unique=False, null=False)
    on_demand = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def execute_scene(self):
        actions = SceneActions.objects.filter(scene=self.id).all()
        for action in actions:
            value = action.value
            if action.variable.type == 'ONOFF':
                action.variable.artifact.change_power(value)
            else:
                action.variable.change_variable(value)
            time.sleep(1)
        return True


class SceneActions(models.Model):
    id = models.AutoField(primary_key=True)
    variable = models.ForeignKey(StateVariable, on_delete=models.DO_NOTHING)
    value = models.CharField(max_length=50, null=False)
    scene = models.ForeignKey(Scene, on_delete=models.DO_NOTHING, related_name='actions')

