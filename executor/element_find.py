import json

def find_all_elements(node):
    elements = []
    elements_json = []
    
    def traverse_node(node):
        if node.get("role") != "none":
            node_without_children = {k: v for k, v in node.items() if k != "children"}

            elements.append(str(node_without_children))
            elements_json.append(node_without_children)
        
        for child in node.get("children", []):
            traverse_node(child)
    
    traverse_node(node)
    
    return elements_json


def process_elements_links_manual(data):
    element_json = find_all_elements(data)

    link_elements = list(filter(lambda element: element.get("role") == "link", element_json))
    link_elements_str = [json.dumps(element) for element in link_elements]

    interactable_elements = []

    filtered_link_elements_str = list(filter(lambda element: "View" in json.loads(element)["name"], link_elements_str))
    interactable_elements.extend(filtered_link_elements_str)

    

    print(interactable_elements)

    return interactable_elements