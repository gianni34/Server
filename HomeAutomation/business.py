# Aca tengo que refactorizar todos los metodos que tengo dispersos por clases incorrectas
# y ponerlos aca como logica de negocio

from HomeAutomation.models import *
import datetime, sched, time, threading

s = sched.scheduler(time.time, time.sleep)


class Main:
    @staticmethod
    def is_execution_day(i):
        scene = Scene.objects.filter(id=i).first()
        string_days = scene.days
        days = string_days.split(',')
        for d in days:
            if d == datetime.datetime.now().weekday():
                return True
        return False

    @staticmethod
    def auto_execution_scene():
        print("Entro al Auto Execution Scene")
        scenes = Scene.objects.all()
        executed = False
        for s in scenes:
            if s.time_condition:
                if Main.is_execution_day(s.id):
                    if s.time == datetime.datetime.now().time():
                        s.execute_scene()
                        executed = True
            if s.value_condition and not executed:
                print("Encontro escena con value condition")
                zone = s.zone
                if zone.temperature > int(s.value):
                    print("Temperatura de la zona mayor al valor de escena")
                    s.execute_scene()
    """"
    @staticmethod
    def scheduler():
        while True:
            s.enter(60, 1, Main.auto_execution_scene)
            s.run()
    """

    @staticmethod
    def delete_actions(i):
        actions = SceneActions.objects.filter(scene=i).all()
        if actions:
            for a in actions:
                SceneActions.delete(a)


class ThreadScheduler(object):

    def __init__(self, interval=60):
        print("Inicializo el Hilo")
        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()

    def run(self):
        while True:
            print("While True de RUN")
            s.enter(60, 1, Main.auto_execution_scene)
            s.run()
