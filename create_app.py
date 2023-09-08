import os
import logging
import requests
import json
import html2text
from datetime import datetime
from dotenv import load_dotenv
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class FireflyInstance():

    def __init__(self) -> None:

        load_dotenv()

        if os.getenv('SCHOOL_CODE'):
            self.school_code = os.getenv('SCHOOL_CODE')
        else:
            logger.debug("SCHOOL_CODE not found in environment variables")
        if os.getenv('HOST'):
            self.host = os.getenv('HOST')
        else:
            logger.debug("HOST not found in environment variables")
        if os.getenv('DEVICE_ID'):
            self.device_id = os.getenv('DEVICE_ID')
        else:
            logger.debug("DEVICE_ID not found in environment variables")
        if os.getenv('SECRET'):
            self.secret = os.getenv('SECRET')
        else:
            logger.debug("SECRET not found in environment variables")
        if os.getenv('NOTION_TOKEN'):
            self.notion_token = os.getenv('NOTION_TOKEN')
        else:
            logger.debug("NOTION_TOKEN not found in environment variables")
        if os.getenv('DATABASE_ID'):
            self.database_id = os.getenv('DATABASE_ID')
        else:
            logger.debug("DATABASE_ID not found in environment variables")

        self.notion_headers = {
            "Authorization": "Bearer " + self.notion_token,
            "Content-Type": "application/json",
            "Notion-Version": "2022-02-22"
        }

    def add_new_todo_tasks_to_notion(self, database_id: str, headers: dict, data: dict):
        createUrl = 'https://api.notion.com/v1/pages'

        for task in data:
            date = datetime.now().strftime("%Y-%m-%d")
            time = datetime.now().strftime("%H:%M:%S")
            firefly_format_time = f"{date}T{time}Z"

            if task['due_date'] < firefly_format_time:
                task['status'] = "Overdue"
            else:
                task['status'] = "To Do"


            if task['attachments']:
                attachment_list = []
                for attachment in task['attachments']:
                    attachment_list.append(f"{self.host}/_api/1.0/tasks/{task['id']}/attachments/{attachment}")
                task['attachments'] = attachment_list

            newPageData = {
                "parent": { "database_id": database_id },
                "properties": {
                    
                    "Title": {
                        "title": [
                            {
                                "text": {
                                    "content": f"{task['title']}"
                                }
                            }
                        ]
                    },

                    "Status": {
                            "status": {
                                "name": f"{task['status']}",
                            }
                        },

                    "Description": {
                            "rich_text": [
                                {
                                    "text": {
                                        "content": f"{task['description']}"
                                    }
                                }
                            ]
                    },

                    "ID": {
                            "rich_text": [
                                {
                                    "text": {
                                        "content": f"{task['id']}"
                                    }
                                }
                            ]
                    },

                    "Due Date": {
                            "date": {
                                "start": f"{task['due_date']}",
                            }
                        },

                    "Attachments": {
                            "url": f"{task['attachments']}",
                    },

                    "Set Date": {
                            "date": {
                                "start": f"{task['set_date']}",
                            }
                        },

                    "Set By": {
                            "select": {
                                "name": f"{task['setter']}",
                            }
                        },

                    "Task Type": {
                            "select": {
                                "name": f"Firefly Task",
                            }
                        },

                    }
                }
            
            data = json.dumps(newPageData)

            res = requests.request("POST", createUrl, headers=headers, data=data)

        # print the status code
        logger.debug(res.status_code)
        # print the error if there is one
        logger.debug(res.json())

    def check_for_existing_tasks(self, database_id: str, headers: dict, data: dict):
        queryUrl = f"https://api.notion.com/v1/databases/{database_id}/query"

        new_tasks = []

        for task in data:
            queryData = {
                "filter": {
                    "property": "ID",
                    "rich_text": {
                    "equals": task['id']
                    }
                }
            }
            data = json.dumps(queryData)

            res = requests.request("POST", queryUrl, headers=headers, data=data)

            if len(res.json()['results']) == 0:
                new_tasks.append(task)

            logger.debug(res.status_code)

        return new_tasks

    def parse_new_todo_tasks(self, task_ids: str, device_id: str, secret: str) -> list[dict[str, str]]:
        info_url = f"{self.host}/api/v2/apps/tasks/byIds?ffauth_device_id={device_id}&ffauth_secret={secret}"
        info_data = {"ids": task_ids}

        info_request = requests.post(info_url, json=info_data)

        list_of_tasks = []
        for idx, task in enumerate(info_request.json()):
            task_dict = {
                "id": str(task['id']),
                "url": f"{self.host}/set-tasks/{task_ids[idx]}",
                "title": task['title'],
                "setter": task['setter']['name'],
                "description": html2text.html2text(task['descriptionDetails']['htmlContent']),
                "set_date": task['setDate'],
                "due_date": task['dueDate'],
                "attachments": [attachment['resourceId'] for attachment in task['fileAttachments']] if task['fileAttachments'] else None,
                "addressees": task['addressees'][0]['principal']['name'] if task['addressees'] else "No group"
            }

            list_of_tasks.append(task_dict)

        return list_of_tasks



    def get_new_todo_tasks(self):
        tasks_url = f"{self.host}/api/v2/taskListing/view/student/tasks/all/filterBy?ffauth_device_id={self.device_id}&ffauth_secret={self.secret}"
        
        tasks_data = {
        "archiveStatus": "All",
        "completionStatus": "Todo",
        "ownerType": "OnlySetters",
        "page": 0,
        "pageSize": 100,
        "sortingCriteria": [
            {
            "column": "DueDate",
            "order": "Descending"
            }
        ]
        }

        tasks_request = requests.post(tasks_url, json=tasks_data)

        task_ids = [task['id'] for task in tasks_request.json()['items']]

        list_of_tasks = self.parse_new_todo_tasks(task_ids, self.device_id, self.secret)

        new_tasks = self.check_for_existing_tasks(self.database_id, self.notion_headers, list_of_tasks)

        self.add_new_todo_tasks_to_notion(self.database_id, self.notion_headers, new_tasks)