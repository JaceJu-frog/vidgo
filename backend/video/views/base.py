# views/base.py
from django.http import JsonResponse
from django.views import View
import json

class JsonView(View):
    """
    • Parses request.body as JSON (if present)
    • Has shortcuts self.json_ok / self.json_err
    """
    data: dict = {}
    # Route actions received by this domain
    def dispatch(self, request, *args, **kwargs):
        if request.body:
            try:
                self.data = json.loads(request.body.decode())
            except json.JSONDecodeError:
                return self.json_err('Invalid JSON', status=400)
        return super().dispatch(request, *args, **kwargs)

    def json_ok(self, payload, status=200):
        return JsonResponse(payload, status=status)

    def json_err(self, message, status=400):
        return JsonResponse({'success': False, 'error': message}, status=status)
