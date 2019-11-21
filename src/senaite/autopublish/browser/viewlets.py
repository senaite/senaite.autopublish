from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from senaite.autopublish.adapters.queue import AUTOPUBLISH_TASK_ID
from senaite.queue.interfaces import IQueued
from senaite.queue.storage import QueueStorageTool
from senaite.autopublish import api
from plone.app.layout.viewlets import ViewletBase


class QueuedSampleViewlet(ViewletBase):
    """Viewlet that displays a message stating the current Sample is queued
    """
    template = ViewPageTemplateFile("templates/queued_sample_viewlet.pt")

    def __init__(self, context, request, view, manager=None):
        super(QueuedSampleViewlet, self).__init__(
            context, request, view, manager=manager)
        self.context = context
        self.request = request
        self.view = QueuedSampleViewlet

    def is_queued_for_autopublish(self):
        """Returns whether the current context is queued for autopublish
        """
        if IQueued.providedBy(self.context):
            qtool = QueueStorageTool()
            uid = api.get_uid(self.context)
            if qtool.get_task(uid, task_name=AUTOPUBLISH_TASK_ID):
                return True
        return False

    def render(self):
        if self.is_queued_for_autopublish():
            return self.template()
        return ""
