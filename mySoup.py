"""
My module for building syntax trees from an html file (The name is inspired from BeautifulSoup)

Example usage:

from mySoup import seed

# First you want to build the syntax tree by calling:
tree_list = seed.build(filename)

# Then, you might want to retrieve objects by accessing specific nodes in the tree.

"""

#list of which html tags do not have subtags (will not have a closing </tag>)
nosub_tags = ["area", "base", "br", "col", "command", "embed", "hr", "iframe" "img", "input", "keygen" "link", "menuitem" "meta", "param", "source", "track", "wbr"]

class seed:
    """
    Wraps static methods to be used outside this module
    Also, this class is a Tree factory
    """
    def __init__(self, arg):
        self.arg = arg

    @staticmethod
    def build(filename, below_tag=None, below_class=None):
        """
        Method to return a list of trees built from the file passed in as parameter
        """
        trees = []
        with open(filename, "r") as file:

            current_tree = Tree()
            char = file.read(1)

            some_text = ""

            while char != "": #Apparently it gets an empty string upon reaching EOF

                if not current_tree.is_open():
                    trees.append(current_tree)
                    current_tree = Tree()

                if char == "<":

                    tag_name = ""
                    tag_params = {}
                    # These 4 are here to help the method store strings correctly
                    tag_key = ""
                    get_value = False
                    tag_value = ""
                    tag_count = 0

                    char = file.read(1)
                    while char != ">":

                        if char == "=":
                            get_value = True

                        if tag_count == 0:
                            tag_name += char
                        else:
                            if get_value:
                                if char not in ["=","\""]:
                                    tag_value += char
                            elif char != " ":
                                tag_key += char

                        if (char == "/") and (tag_name[0] == "/") and current_tree.is_open() and tag_count == 0:
                            current_tree.add_text(some_text)

                        previous = char
                        char = file.read(1)

                        if char in [" ", ">"]:
                            tag_count += 1
                            if get_value:
                                if previous == "\"":
                                    tag_params[tag_key] = tag_value
                                    tag_key = ""
                                    tag_value = ""
                                    get_value = False
                                else:
                                    tag_count -= 1

                    if current_tree.root is not None: # If the tree already has a root, keep going deeper
                        current_tree.add_htmltag(tag_name, tag_params)
                    elif below_class:
                        if "class" in tag_params.keys():
                            if (tag_params["class"] == below_class):
                                current_tree.add_htmltag(tag_name, tag_params)
                    elif below_tag:
                        if (tag_name == below_tag) or (current_tree.root is not None):
                            current_tree.add_htmltag(tag_name, tag_params)
                    else: # If no special parameter was specified, this will add the root
                        current_tree.add_htmltag(tag_name, tag_params)

                    some_text = ""

                elif char != "\n":
                    some_text += char

                char = file.read(1)

            if current_tree.is_open():
                print("Bracket closings have some weird stuff going on")

            if current_tree.root: # This condition is to prevent adding an empty tree when the file ends with extra spaces/end of line
                trees.append(current_tree)
        return trees

    @staticmethod
    def view(tree, deep=False):
        """
        This method prints the given tree to the terminal
        It is more of a debugging tool
        If deep is set to true, params for every node will also be printed
        """
        seed._view(tree.root, 0, deep=deep)

    @staticmethod
    def _view(node, lvl, deep=False):
        """Internal method to recursively traverse the tree below the given node, printing its contents"""
        ident = "    " * lvl
        print(f"{ident}{node.name}, level {lvl}")
        if deep:
            print_dict(node.params, ident=ident)

        if node.subordinates:
            for sub in node.subordinates:
                seed._view(sub, lvl + 1, deep=deep)

def print_dict(dictionary, ident=""):
    """Special print function for dictionaries"""
    for key, value in dictionary.items():
        print(f"{ident} ::{key} = {value}")

class Tree:
    """
    This class is a node factory:
    Node objects should always be retrieved through this class
    """
    def __init__(self):
        self.current_node = None
        self.root = None

    def new_node(self, tagname, **params):
        """
        Method to create a new node in this tree
        self.current_node will change into the newly created node automatically
        """
        if not self.current_node:
            leaf = Node(tagname, None, **params)
            self.root = leaf
            self.current_node = self.root
        else:
            leaf = Node(tagname, self.current_node, **params)
            self.current_node.addsub(leaf)
            self.current_node = leaf

    def close_node(self):
        """Return to the previous boss node"""
        self.current_node = self.current_node.boss

    def is_open(self):
        """
        Returns false if a tree has been completely built, true otherwise
        In other words, returns true if the tree is still being built
        """
        return not ((self.current_node is None) and (self.root is not None))

    def add_htmltag(self, tag_name, tag_params):
        """
        Internal method to parse html node insertion into the tree
        """
        if tag_name in nosub_tags:
            self.new_node(tag_name, **tag_params)
            self.close_node()
        elif tag_name[0] == "/":
            self.close_node()
        else:
            self.new_node(tag_name, **tag_params)

    def add_text(self, text):
        """
        Helper that adds a text parameter to the node
        I'm still evaluating if empty text should not be added
        """
        if self.current_node:
            #if text != "":
            self.current_node.params["text"] = text

    def find(self, **search_args):
        """Helper for calling the node.find() method in the whole tree"""
        return self.root.find(**search_args)

    def find_all(self, **search_args):
        """Helper for calling the node.find_all() method in the whole tree"""
        return self.root.find_all(**search_args)

class Node:
    """A Syntax Tree node"""
    def __init__(self, tagname, boss, **params):
        self.name = tagname
        self.boss = boss
        self.subordinates = None
        self.params = params

    def addsub(self, sub):
        """Method to register a subnode"""
        if not self.subordinates:
            self.subordinates = []
        self.subordinates.append(sub)

    def is_root(self):
        """Bool to verify if this node is the root node"""
        return self.boss is None

    def get(self, key):
        """
        Helper to get data from a node
        Remember that most/all keys are stored as strings, so the key parameter should be a string
        """
        return self.params[key]

    def has_subs(self):
        """Returns true if this node can have subnodes"""
        return self.name in sub_tags

    def find(self, **search_args):
        """
        Returns the first node that matches the search parameter specified.
        Will dig down in subnodes recursively
        Will return None if no result is found
        """
        if self.name == search_args.get("name"):
            return self
        for key, value in search_args:
            if self.params[key] == value:
                return self
        if self.subordinates:
            for sub in self.subordinates:
                result = sub.find(**search_args)
                if result is not None:
                    return result
        return None

    def find_all(self, **search_args):
        """
        Returns a list with all nodes that match the search parameter specified.
        Will dig down in subnodes recursively
        Will return an empty list if no result is found
        """
        result = []
        if self.name == search_args.get("name"):
            result.append(self)
        for key, value in search_args:
            if self.params[key] == value:
                result.append(self)
        if self.subordinates:
            for sub in self.subordinates:
                sub_result = sub.find_all(**search_args)
                result.extend(sub_result)
        return result

test = seed.build("arquivo.html", below_class="controls")

print(test)

for t in test:
    seed.view(t, deep=True)
