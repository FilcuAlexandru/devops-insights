{{/* Release-scoped name used as the prefix of every resource. */}}
{{- define "di.fullname" -}}
{{- if contains .Chart.Name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name .Chart.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{/* Labels attached to every resource. */}}
{{- define "di.labels" -}}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version }}
app.kubernetes.io/name: {{ .Chart.Name }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{/* Labels that select the pods of one component. Usage: include "di.selector" (dict "root" . "component" "backend") */}}
{{- define "di.selector" -}}
app.kubernetes.io/name: {{ .root.Chart.Name }}
app.kubernetes.io/instance: {{ .root.Release.Name }}
app.kubernetes.io/component: {{ .component }}
{{- end -}}

{{/* image:tag. Usage: include "di.image" (dict "root" . "image" .Values.backend.image) */}}
{{- define "di.image" -}}
{{- printf "%s:%s" .image.repository (.image.tag | default .root.Chart.AppVersion | toString) -}}
{{- end -}}

{{/* Service name of one component. Usage: include "di.service" (dict "root" . "component" "backend") */}}
{{- define "di.service" -}}
{{- printf "%s-%s" (include "di.fullname" .root) .component -}}
{{- end -}}

{{/* SQLAlchemy URL of the database used by the backend and the collector. */}}
{{- define "di.databaseUrl" -}}
{{- if .Values.postgresql.enabled -}}
{{- $auth := .Values.postgresql.auth -}}
{{- printf "postgresql+psycopg://%s:%s@%s:%v/%s" (urlquery $auth.username) (urlquery $auth.password) (include "di.service" (dict "root" . "component" "postgresql")) .Values.postgresql.service.port $auth.database -}}
{{- else -}}
{{- required "externalDatabase.url is required when postgresql.enabled is false" .Values.externalDatabase.url -}}
{{- end -}}
{{- end -}}

{{/*
Public address of a component. Explicit values under `links` win; otherwise, when Routes
are enabled, the address is derived from the route host. Usage:
  include "di.link" (dict "root" . "key" "grafana" "component" "grafana")
*/}}
{{- define "di.link" -}}
{{- $explicit := index .root.Values.links .key -}}
{{- if $explicit -}}
{{- $explicit -}}
{{- else if and .root.Values.route.enabled .root.Values.route.appsDomain .component -}}
{{- $suffix := ternary "/api/docs" "" (eq .key "apiDocs") -}}
{{- printf "https://%s-%s.%s%s" .component .root.Release.Namespace .root.Values.route.appsDomain $suffix -}}
{{- end -}}
{{- end -}}

{{/* Environment shared by the migration step, the backend and the collector. */}}
{{- define "di.backendEnv" -}}
- name: DATABASE_URL
  valueFrom:
    secretKeyRef:
      name: {{ include "di.service" (dict "root" . "component" "backend") }}
      key: DATABASE_URL
- name: GITHUB_TOKEN
  valueFrom:
    secretKeyRef:
      name: {{ include "di.service" (dict "root" . "component" "backend") }}
      key: GITHUB_TOKEN
- name: APP_ENV
  value: production
- name: LOG_LEVEL
  value: {{ .Values.backend.logLevel | quote }}
{{- if .Values.ollama.enabled }}
- name: OLLAMA_BASE_URL
  value: {{ printf "http://%s:%v" (include "di.service" (dict "root" . "component" "ollama")) .Values.ollama.service.port | quote }}
- name: OLLAMA_MODEL
  value: {{ .Values.ollama.model | quote }}
{{- end }}
{{- end -}}

{{/* Init container that waits for PostgreSQL and applies migrations. */}}
{{- define "di.migrateContainer" -}}
- name: migrate
  image: {{ include "di.image" (dict "root" . "image" .Values.backend.image) }}
  imagePullPolicy: {{ .Values.backend.image.pullPolicy }}
  command: [python, -m, devops_insights.migrate]
  securityContext:
    {{- toYaml .Values.containerSecurityContext | nindent 4 }}
  env:
    {{- include "di.backendEnv" . | nindent 4 }}
  resources:
    requests: { cpu: 25m, memory: 64Mi }
    limits: { cpu: 250m, memory: 192Mi }
{{- end -}}
