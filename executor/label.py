workman_id_generator = """
            ({ iframe_path, current_tf_id }) => {
              IDGenerator = class {
                constructor() {
                  this.currentID = current_tf_id || 0;
                }

                getNextID() {
                  this.currentID += 1;
                  return this.currentID;
                }
              };

              const _tf_id_generator = new window.IDGenerator();

              function extractAttributes(node) {
                const attributes = { html_tag: node.nodeName.toLowerCase() };
                const skippedAttributes = ['style', 'srcdoc'];

                for (let i = 0; i < node.attributes.length; i++) {
                  const attribute = node.attributes[i];
                  if (!attribute.specified || !skippedAttributes.includes(attribute.name)) {
                    attributes[attribute.name] = attribute.value.slice(0, 100) || true;
                  }
                }

                return attributes;
              }

              function pre_process_dom_node(node) {
                if (!node) {
                  return;
                }
                if (node.hasAttribute('aria-keyshortcuts')) {
                  try {
                    ariaKeyShortcuts = JSON.parse(node.getAttribute('aria-keyshortcuts'));
                    if (ariaKeyShortcuts.hasOwnProperty('html_tag')) {
                      if (ariaKeyShortcuts.hasOwnProperty('aria-keyshortcuts')) {
                        ariaKeyShortcutsInsideAriaKeyShortcuts =
                          ariaKeyShortcuts['aria-keyshortcuts'];
                        node.setAttribute(
                          'aria-keyshortcuts',
                          ariaKeyShortcutsInsideAriaKeyShortcuts
                        );
                      } else {
                        node.removeAttribute('aria-keyshortcuts');
                      }
                    }
                  } catch (e) {
                    //aria-keyshortcuts is not a valid json, proceed with current aria-keyshortcuts value
                  }
                }

                let currentChildNodes = node.childNodes;
                if (node.shadowRoot) {
                    const childrenNodeList = Array.from(node.shadowRoot.children);

                    if (childrenNodeList.length > 0) {
                        currentChildNodes = Array.from(childrenNodeList);
                    } else if (node.shadowRoot.textContent.trim() !== '') {
                        node.setAttribute('aria-label', node.shadowRoot.textContent.trim());
                    }
                } else if (node.tagName === 'SLOT') {
                    currentChildNodes = node.assignedNodes({ flatten: true });
                }

                if (!node.hasAttribute('workman_id')) {
                  const tfId = _tf_id_generator.getNextID();
                  node.setAttribute('workman_id', tfId);
                }

                if (iframe_path) {
                    node.setAttribute('iframe_path', iframe_path);
                }
                node.setAttribute(
                    'aria-keyshortcuts',
                    JSON.stringify(extractAttributes(node))
                );

                const childNodes = Array.from(currentChildNodes).filter((childNode) => {
                  return (
                    childNode.nodeType === Node.ELEMENT_NODE ||
                    (childNode.nodeType === Node.TEXT_NODE &&
                      childNode.textContent.trim() !== '')
                  );
                });
                for (let i = 0; i < childNodes.length; i++) {
                  let childNode = childNodes[i];
                  if (childNode.nodeType === Node.TEXT_NODE) {
                    const text = childNode.textContent.trim();
                    if (text) {
                      if (childNodes.length > 1) {
                        const span = document.createElement('span');
                        span.textContent = text;
                        node.insertBefore(span, childNode);
                        node.removeChild(childNode);
                        childNode = span;
                      } else if (!node.hasAttribute('aria-label')) {
                        const structureTags = [
                          'a',
                          'button',
                          'h1',
                          'h2',
                          'h3',
                          'h4',
                          'h5',
                          'h6',
                          'script',
                          'style',
                        ];
                        if (!structureTags.includes(node.nodeName.toLowerCase())) {
                          node.setAttribute('aria-label', text);
                        }
                      }
                    }
                  }
                  if (childNode.nodeType === Node.ELEMENT_NODE) {
                    pre_process_dom_node(childNode);
                  }
                }
              }
              pre_process_dom_node(document.documentElement);
              return _tf_id_generator.currentID;
            };
"""
