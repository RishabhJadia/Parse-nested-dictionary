from django.db import models

class SealTable(models.Model):
    seal = models.CharField(max_length=255)
    deployment = models.CharField(max_length=255)

class JobMask(models.Model):
    job = models.CharField(max_length=255)
    sealid = models.ForeignKey(SealTable, on_delete=models.CASCADE, related_name='job_masks')

class InstanceJobMask(models.Model):
    instance = models.ForeignKey('InstanceTable', on_delete=models.CASCADE)
    jobmask = models.ForeignKey(JobMask, on_delete=models.CASCADE)
    additional_field = models.CharField(max_length=255, null=True, blank=True)  # Example of additional field

class InstanceTable(models.Model):
    instance = models.CharField(max_length=255)
    jobmask = models.ManyToManyField(JobMask, through='InstanceJobMask', related_name='instances')
    environment = models.CharField(max_length=255)

class AgentHost(models.Model):
    host = models.ForeignKey('HostTable', on_delete=models.CASCADE)
    agent = models.ForeignKey('AgentTable', on_delete=models.CASCADE)
    additional_field = models.CharField(max_length=255, null=True, blank=True)  # Example of additional field

class AgentTable(models.Model):
    agent = models.CharField(max_length=255)
    version = models.CharField(max_length=255)

class HostTable(models.Model):
    host = models.CharField(max_length=255)
    agent_name = models.ManyToManyField(AgentTable, through='AgentHost', related_name='agent_hosts')
    environment = models.CharField(max_length=255)
    instance = models.ForeignKey(InstanceTable, on_delete=models.CASCADE, related_name='instance_hosts')

class MachineHost(models.Model):
    machine = models.ForeignKey('MachineTable', on_delete=models.CASCADE)
    host = models.ForeignKey('HostTable', on_delete=models.CASCADE)
    additional_field = models.CharField(max_length=255, null=True, blank=True)  # Example of additional field

class MachineTable(models.Model):
    machine = models.CharField(max_length=255)
    host = models.ManyToManyField(HostTable, through='MachineHost', related_name='machine_hosts')

class JobConfig(models.Model):
    job = models.CharField(max_length=255)
    machine = models.ForeignKey(MachineTable, on_delete=models.CASCADE, related_name='job_configs')
