

class Column(object):
    def __init__(self, project_id, input_dict: dict):
        self.project_id = project_id
        self.name = input_dict['name']
        self.id = input_dict['id']
