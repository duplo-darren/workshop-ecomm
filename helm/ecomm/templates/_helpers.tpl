{{/*
Chart name.
*/}}
{{- define "ecomm.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Fully qualified release name.
*/}}
{{- define "ecomm.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{- define "ecomm.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Labels shared by every object.
*/}}
{{- define "ecomm.labels" -}}
helm.sh/chart: {{ include "ecomm.chart" . }}
app.kubernetes.io/name: {{ include "ecomm.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: ecomm
{{- with .Values.commonLabels }}
{{ toYaml . }}
{{- end }}
{{- end -}}

{{/*
Selector labels for one component. Usage: include "ecomm.selectorLabels" (dict "ctx" $ "component" "catalog")
*/}}
{{- define "ecomm.selectorLabels" -}}
app.kubernetes.io/name: {{ include "ecomm.name" .ctx }}
app.kubernetes.io/instance: {{ .ctx.Release.Name }}
app.kubernetes.io/component: {{ .component }}
{{- end -}}

{{- define "ecomm.componentLabels" -}}
{{ include "ecomm.labels" .ctx }}
app.kubernetes.io/component: {{ .component }}
{{- end -}}

{{/*
Image reference for a service. Usage: include "ecomm.image" (dict "ctx" $ "service" "catalog" "svcValues" .Values.catalog)
Resolution order: per-service repository -> "<registry>/<repositoryPrefix>-<service>".
*/}}
{{- define "ecomm.image" -}}
{{- $ctx := .ctx -}}
{{- $global := $ctx.Values.image -}}
{{- $svc := .svcValues -}}
{{- $repo := "" -}}
{{- if and $svc.image $svc.image.repository -}}
{{- $repo = $svc.image.repository -}}
{{- else -}}
{{- $repo = printf "%s-%s" $global.repositoryPrefix .service -}}
{{- if $global.registry -}}
{{- $repo = printf "%s/%s" (trimSuffix "/" $global.registry) $repo -}}
{{- end -}}
{{- end -}}
{{- $tag := $global.tag -}}
{{- if and $svc.image $svc.image.tag -}}
{{- $tag = $svc.image.tag -}}
{{- end -}}
{{- printf "%s:%s" $repo $tag -}}
{{- end -}}

{{/*
Service account name for a component.
*/}}
{{- define "ecomm.serviceAccountName" -}}
{{- $svc := .svcValues -}}
{{- if $svc.serviceAccount.create -}}
{{- default (printf "%s-%s" (include "ecomm.fullname" .ctx) .component) $svc.serviceAccount.name -}}
{{- else -}}
{{- default "default" $svc.serviceAccount.name -}}
{{- end -}}
{{- end -}}

{{/*
In-cluster PostgreSQL host / secret names.
*/}}
{{- define "ecomm.postgres.fullname" -}}
{{- printf "%s-postgres" (include "ecomm.fullname" .) -}}
{{- end -}}

{{- define "ecomm.postgres.secretName" -}}
{{- if .Values.postgres.auth.existingSecret -}}
{{- .Values.postgres.auth.existingSecret -}}
{{- else -}}
{{- include "ecomm.postgres.fullname" . -}}
{{- end -}}
{{- end -}}

{{/*
Name of the secret holding the per-service DATABASE_URL values.
*/}}
{{- define "ecomm.dbSecretName" -}}
{{- printf "%s-db" (include "ecomm.fullname" .) -}}
{{- end -}}

{{/*
Whether any service supplies an explicit databaseUrl that needs a chart-managed
secret.
*/}}
{{- define "ecomm.needsDbSecret" -}}
{{- if or (and .Values.catalog.enabled .Values.catalog.databaseUrl (not .Values.catalog.existingSecret)) (and .Values.inventory.enabled .Values.inventory.databaseUrl (not .Values.inventory.existingSecret)) -}}
true
{{- end -}}
{{- end -}}

{{/*
Database environment variables for catalog/inventory, in precedence order:
  1. existingSecret        -> DATABASE_URL read from a user-managed secret
  2. databaseUrl           -> DATABASE_URL read from the chart-managed secret
  3. postgres.enabled      -> DATABASE_URL composed from the in-cluster credentials
  4. otherwise             -> AWS Secrets Manager lookup done by the app itself
Usage: include "ecomm.dbEnv" (dict "ctx" $ "component" "catalog" "svcValues" .Values.catalog "database" "ecomm_catalog")
*/}}
{{- define "ecomm.dbEnv" -}}
{{- $ctx := .ctx -}}
{{- $svc := .svcValues -}}
{{- if $svc.existingSecret }}
- name: DATABASE_URL
  valueFrom:
    secretKeyRef:
      name: {{ $svc.existingSecret }}
      key: {{ $svc.existingSecretKey }}
{{- else if $svc.databaseUrl }}
- name: DATABASE_URL
  valueFrom:
    secretKeyRef:
      name: {{ include "ecomm.dbSecretName" $ctx }}
      key: {{ .component }}-database-url
{{- else if $ctx.Values.postgres.enabled }}
- name: DB_USERNAME
  valueFrom:
    secretKeyRef:
      name: {{ include "ecomm.postgres.secretName" $ctx }}
      key: username
- name: DB_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ include "ecomm.postgres.secretName" $ctx }}
      key: password
- name: DATABASE_URL
  value: "postgresql://$(DB_USERNAME):$(DB_PASSWORD)@{{ include "ecomm.postgres.fullname" $ctx }}:{{ $ctx.Values.postgres.service.port }}/{{ .database }}"
{{- else }}
{{- with $svc.aws.dbSecretName }}
- name: DB_SECRET_NAME
  value: {{ . | quote }}
{{- end }}
{{- with $svc.aws.dbName }}
- name: DB_NAME
  value: {{ . | quote }}
{{- end }}
{{- end }}
{{- with $svc.aws.region }}
- name: AWS_REGION
  value: {{ . | quote }}
{{- end }}
{{- end -}}

{{/*
Init container that blocks until PostgreSQL accepts connections. Only meaningful
when the in-cluster database is enabled, so call sites guard on
.Values.postgres.enabled.
*/}}
{{- define "ecomm.waitForDb" -}}
- name: wait-for-db
  image: "{{ .Values.waitForDb.image.repository }}:{{ .Values.waitForDb.image.tag }}"
  imagePullPolicy: {{ .Values.waitForDb.image.pullPolicy }}
  command:
    - sh
    - -c
    - |
      deadline=$(( $(date +%s) + {{ .Values.waitForDb.timeoutSeconds }} ))
      until pg_isready -h {{ include "ecomm.postgres.fullname" . }} -p {{ .Values.postgres.service.port }} -U {{ .Values.postgres.auth.username }} -q; do
        if [ "$(date +%s)" -ge "$deadline" ]; then
          echo "Timed out waiting for PostgreSQL" >&2
          exit 1
        fi
        echo "Waiting for PostgreSQL at {{ include "ecomm.postgres.fullname" . }}:{{ .Values.postgres.service.port }} ..."
        sleep 3
      done
      echo "PostgreSQL is ready."
  resources:
    {{- toYaml .Values.waitForDb.resources | nindent 4 }}
  securityContext:
    {{- toYaml .Values.securityContext | nindent 4 }}
{{- end -}}
