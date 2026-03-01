{
  "name": "Finder AI - Basic Research Workflow",
  "nodes": [
    {
      "parameters": {
        "httpMethod": "POST",
        "path": "finder-research",
        "responseMode": "lastNode",
        "options": {}
      },
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "typeVersion": 1,
      "position": [250, 300],
      "webhookId": "finder-webhook-1"
    },
    {
      "parameters": {
        "method": "POST",
        "url": "http://localhost:8000/api/v2/webhook",
        "jsonParameters": true,
        "options": {},
        "bodyParametersJson": "={\n  \"query\": \"{{ $json.query }}\",\n  \"session_id\": \"{{ $json.session_id || 'n8n-' + $now.toISO() }}\",\n  \"metadata\": {\n    \"source\": \"n8n\",\n    \"workflow_id\": \"basic-research\"\n  }\n}"
      },
      "name": "Finder API",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 3,
      "position": [470, 300],
      "retryOnFail": true,
      "maxTries": 3,
      "waitBetweenTries": 1000
    },
    {
      "parameters": {
        "conditions": {
          "boolean": [
            {
              "value1": "={{ $json.success }}",
              "value2": true
            }
          ]
        }
      },
      "name": "Check Success",
      "type": "n8n-nodes-base.if",
      "typeVersion": 1,
      "position": [690, 300]
    },
    {
      "parameters": {
        "values": {
          "string": [
            {
              "name": "timestamp",
              "value": "={{ $now.toISO() }}"
            },
            {
              "name": "query",
              "value": "={{ $node[\"Webhook\"].json.query }}"
            },
            {
              "name": "response",
              "value": "={{ $json.response }}"
            },
            {
              "name": "session_id",
              "value": "={{ $json.session_id }}"
            },
            {
              "name": "sources_count",
              "value": "={{ $json.sources.length }}"
            }
          ]
        },
        "options": {}
      },
      "name": "Format Success",
      "type": "n8n-nodes-base.set",
      "typeVersion": 1,
      "position": [890, 200]
    },
    {
      "parameters": {
        "values": {
          "string": [
            {
              "name": "error",
              "value": "Research failed"
            },
            {
              "name": "query",
              "value": "={{ $node[\"Webhook\"].json.query }}"
            },
            {
              "name": "timestamp",
              "value": "={{ $now.toISO() }}"
            }
          ]
        },
        "options": {}
      },
      "name": "Format Error",
      "type": "n8n-nodes-base.set",
      "typeVersion": 1,
      "position": [890, 400]
    }
  ],
  "connections": {
    "Webhook": {
      "main": [
        [
          {
            "node": "Finder API",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Finder API": {
      "main": [
        [
          {
            "node": "Check Success",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Check Success": {
      "main": [
        [
          {
            "node": "Format Success",
            "type": "main",
            "index": 0
          }
        ],
        [
          {
            "node": "Format Error",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  },
  "settings": {},
  "staticData": null,
  "tags": ["finder-ai", "research", "ai-agent"],
  "triggerCount": 1,
  "updatedAt": "2024-01-01T00:00:00.000Z",
  "versionId": "1"
}