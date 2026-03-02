class Job:
    def __init__(self, total):
        self.total = total
        self.count = 0
        self.done = False
        self.interrupt = False


class Observable():
    def __init__(self):
        self.job: Job = None
        self.observers = []
        self.status_message = None

    def set_status(self, message):
        self.status_message = message
        self.notifyObservers()

    def startJob(self, total):
        self.job = Job(total)
        self.status_message = None
        self.notifyObservers()

    def updateJob(self, increment, data=None):
        if not self.job is None:
            self.job.count += increment
            if self.job.count >= self.job.total:
                self.job.done = True

        self.notifyObservers(increment, data)

    def notifyObservers(self, increment=0, data=None):
        for observer in self.observers:
            observer(
                self.job.total if self.job else 0,
                increment,
                self.job.count if self.job else 0,
                self.job.done if self.job else False,
                data,
                self.status_message)

    def requestInterrupt(self):
        self.job.interrupt = True

    def shouldInterrupt(self):
        return self.job.interrupt

    def addObserver(self, observer):
        self.observers.append(observer)

    def removeObserver(self, observer):
        self.observers.remove(observer)
