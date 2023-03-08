{{- define "test-server-chart.deployment.gpu-tester.labels" -}}
app: superqa
{{- end }}
{{- define "test-server-chart.service.gpu-tester.labels" -}}
app: superqa
{{- end }}
{{- define "test-server-chart.namespace.labels" -}}
openpolicyagent.org/webhook: ignore
{{- end }}
{{- define "test-server-chart.virtual-server.annotations" -}}
kubernetes.io/ingress.class: nginx
{{- end }}