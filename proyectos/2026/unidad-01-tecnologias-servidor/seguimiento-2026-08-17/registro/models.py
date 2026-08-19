from django.db import models

class Michi(models.Model):
    nombre = models.CharField(max_length=50)
    tipo = models.CharField(max_length=50) 
    
    def __str__(self):
        return self.nombre