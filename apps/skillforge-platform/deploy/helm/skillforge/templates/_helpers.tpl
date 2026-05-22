{{- define "skillforge.name" -}}
skillforge
{{- end -}}

{{- define "skillforge.labels" -}}
app.kubernetes.io/name: {{ include "skillforge.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version | replace "+" "_" }}
{{- end -}}

{{- define "skillforge.selectorLabels" -}}
app.kubernetes.io/name: {{ include "skillforge.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
