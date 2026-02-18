Update an Incident Workflow
put
https://api.pagerduty.com/incident_workflows/{id}
Update an Incident Workflow

An Incident Workflow is a sequence of configurable Steps and associated Triggers that can execute automated Actions for a given Incident.

Scoped OAuth requires: incident_workflows.write

Request
Path Parameters
id
string
required
The ID of the resource.

Headers
Accept
string
required
The Accept header is used as a versioning header.

Default:
application/vnd.pagerduty+json;version=2
Content-Type
string
required
Allowed value:
application/json
Default:
application/json
Body

application/json

application/json
incident_workflow
object
required
name
string
A descriptive name for the Incident Workflow

description
string
A description of what the Incident Workflow does

team
object
If specified then workflow edit permissions will be scoped to members of this team

is_enabled
boolean
Indicates whether the Incident Workflow is enabled or not. Disabled workflows will not be triggered, and will not count toward the account's enabled workflow limit.

Default:
true
steps
array[object]
The ordered list of steps that execute sequentially as part of the workflow

Responses
200
400
401
402
403
404
429
The changed Incident Workflow

Body

application/json

application/json
incident_workflow
object
required
id
string
summary
string or null
A short-form, server-generated string that provides succinct, important information about an object suitable for primary labeling of an entity in a client. In many cases, this will be identical to name, though it is not intended to be an identifier.

type
string
A string that determines the schema of the object. This must be the standard name for the entity, suffixed by _reference if the object is a reference.

Allowed value:
incident_workflow
self
string<url> or null
the API show URL at which the object is accessible

html_url
string<url> or null
a URL at which the entity is uniquely displayed in the Web app

name
string
A descriptive name for the Incident Workflow

description
string
A description of what the Incident Workflow does

created_at
string<date-time>
The timestamp this Incident Workflow was created

team
object
If specified then workflow edit permissions will be scoped to members of this team

is_enabled
boolean
Indicates whether the Incident Workflow is enabled or not. Disabled workflows will not be triggered, and will not count toward the account's enabled workflow limit.

Default:
true
steps
array[object]
The ordered list of steps that execute sequentially as part of the workflow

Authorization
:
Token token=y_NbAkKc66ryYTWUXYEu
id*
:
string
Accept*
:
application/vnd.pagerduty+json;version=2
Content-Type*
:

application/json

application/json
{
  "incident_workflow": {
    "name": "Example Incident Workflow",
    "description": "This Incident Workflow is an example",
    "steps": [
      {
        "name": "Send Status Update",
        "action_configuration": {
          "action_id": "pagerduty.com:incident-workflows:send-status-update:1",
          "inputs": [
            {
              "name": "Message",
              "value": "Example status message sent on {{current_date}}"
            }
          ]
        }
      }
    ]
  }
}
{
  "incident_workflow": {
    "name": "Example Incident Workflow",
    "description": "This Incident Workflow is an example",
    "steps": [
      {
        "name": "Send Status Update",
        "action_configuration": {
          "action_id": "pagerduty.com:incident-workflows:send-status-update:1",
          "inputs": [
            {
              "name": "Message",
              "value": "Example status message sent on {{current_date}}"
            }
          ]
        }
      }
    ]
  }
}
Send API Request

PagerDuty V2 API.
curl --request PUT \
  --url https://api.pagerduty.com/incident_workflows/{id} \
  --header 'Accept: application/json' \
  --header 'Authorization: Token token=y_NbAkKc66ryYTWUXYEu' \
  --header 'Content-Type: application/json' \
  --data '{
  "incident_workflow": {
    "name": "Example Incident Workflow",
    "description": "This Incident Workflow is an example",
    "steps": [
      {
        "name": "Send Status Update",
        "action_configuration": {
          "action_id": "pagerduty.com:incident-workflows:send-status-update:1",
          "inputs": [
            {
              "name": "Message",
              "value": "Example status message sent on {{current_date}}"
            }
          ]
        }
      }
    ]
  }
}'
{
  "incident_workflow": {
    "id": "PSFEVL7",
    "name": "Example Incident Workflow",
    "description": "This Incident Workflow is an example",
    "type": "incident_workflow",
    "created_at": "2022-12-13T19:55:01.171Z",
    "self": "https://api.pagerduty.com/incident_workflows/PSFEVL7",
    "html_url": "https://pdt-flex-actions.pagerduty.com/flex-workflows/workflows/PSFEVL7",
    "steps": [
      {
        "id": "P4RG7YW",
        "type": "step",
        "name": "Send Status Update",
        "description": "Posts a status update to a given incident",
        "action_configuration": {
          "action_id": "pagerduty.com:incident-workflows:send-status-update:1",
          "description": "Posts a status update to a given incident",
          "inputs": [
            {
              "name": "Message",
              "parameter_type": "text",
              "value": "Example status message sent on {{current_date}}"
            }
          ],
          "outputs": [
            {
              "name": "Result",
              "reference_name": "result",
              "parameter_type": "text"
            },
            {
              "name": "Result Summary",
              "reference_name": "result-summary",
              "parameter_type": "text"
            },
            {
              "name": "Error",
              "reference_name": "error",
              "parameter_type": "text"
            }
          ]
        }
      }
    ]
  }
}