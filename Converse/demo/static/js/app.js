/////////////////////util/////////////////////
let window_width = (window.innerWidth > 0) ? window.innerWidth : screen.width;
(function ($) {
    $.getQuery = function (query, url) {
        query = query.replace(/[\[]/, "\\\[").replace(/[\]]/, "\\\]");
        let expr = "[\\?&]" + query + "=([^&#]*)";
        let regex = new RegExp(expr);
        let results = regex.exec(url);
        if (results !== null) {
            return results[1];
        } else {
            return '';
        }
    };
})(jQuery);


let ID = function () {
    return '_' + Math.random().toString(36).substr(2, 9);
};
let file = $.getQuery('file', window.location.href);
let ts = $.getQuery('ts', window.location.href);

$.template("text", "<div class='form-group ${type} '><label for='${id}' ><span>${id}</span> </label> <input type='${type}' value='${value}' class='form-control' id='${id}' name='${id}'></div>");

$.template("textarea", "<div class='textarea form-group'><label for='${id}' ><span>${id}</span> </label> <textarea  class='form-control' id='${id}' rows=3  cols='30' name='${id}'  wrap='soft'>${value}</textarea> </div>");

$.template("select", "<div class='form-group select'><label for='${id}'><span>${id}</span> </label><select name='${id}' id='${id}' class='selectpicker' value='${value}'><option></option>{{each options}}<option value='${$value}'>${$value}</option>{{/each}}</select> </div>");

$.template("multiselect", "<div class='multiselect  ${cls}'><label for='${id}' ><span>${id}</span> </label> <select name='${id}' id='${id}' class='form-control bsmultiselect' multiple=multiple  size=4>{{each select}}<option value='${$value}'>${$value}</option>{{/each}}</select> </div>");

$.template("datalist", "<div class='form-group datalist'><label for='${id}'><span>${id}</span> </label> <input type='${type}' value='${value}' list='${id}_dl' class='form-control' id='${id}' name='${id}'>  <datalist name='${id}_dl' id='${id}_dl' class='' ><option></option>{{each options}}<option value='${$value}'>{{/each}}</datalist> </div>");

let setMsg = function (msg, type = 'success') {
    let delay = 2000;
    if (type == 'danger') {
        delay = 90000;
    }

    if (msg == 'Please login') {
        window.location.replace('login.php?url=index.php');
        return;
    }


    $.bootstrapGrowl(msg, {
        type: type,
        delay: delay,
    });
};

function copy(l) {
    return JSON.parse(JSON.stringify(l));
}

function open_popup(url) {
    let w = 880;
    let h = 570;
    let l = Math.floor((screen.width - w) / 2);
    let t = Math.floor((screen.height - h) / 2);
    let win = window.open(url, 'ResponsiveFileManager', "scrollbars=1,width=" + w + ",height=" + h + ",top=" + t + ",left=" + l);
}


let choice = function (heading, question, choice1ButtonTxt, choice2ButtonTxt, callback1, callback2) {

    let confirmModal = $('<div class="modal fade" tabindex="-1" id="confirmdialog" role="dialog"><div class="modal-dialog"><div class="modal-content"><div class="modal-header"><button type="button" class="close" data-dismiss="modal">&times;</button><h4 class="modal-title">'
        + heading + '</h4><div class="modal-body"><p>'
        + question + '</p></div></div><div class="modal-footer"><button type="button" class="btn btn-default" data-dismiss="modal" id="btn1">'
        + choice1ButtonTxt + '</button><button type="button" class="btn btn-default" data-dismiss="modal" id="btn2" >'
        + choice2ButtonTxt + '</button></div></div></div></div>');

    confirmModal.find('#btn1').click(function (event) {
        confirmModal.modal('hide');
        callback1 && callback1();
    });

    confirmModal.find('#btn2').click(function (event) {
        confirmModal.modal('hide');
        callback2 && callback2();
    });

    confirmModal.modal('show');
};


let selectPrompt = function (question, list, callback) {
    let select = '<select id="modal_select"><option></option>';
    for (let i = 0; i < list.length; ++i) {
        select += '<option>' + list[i] + '</option>';
    }
    select += '</select>';
    let confirmModal = $('<div class="modal fade" tabindex="-1" id="confirmdialog" role="dialog"><div class="modal-dialog"><div class="modal-content"><div class="modal-header"><button type="button" class="close" data-dismiss="modal">&times;</button><h4 class="modal-title">'
        + question + '</h4><div class="modal-body"><p>'
        + select + '</p></div></div><div class="modal-footer"> </div></div></div></div>');

    confirmModal.find('#modal_select').change(function (event) {
        confirmModal.modal('hide');
        callback && callback($(this).val());
    });


    confirmModal.modal('show');
};

let xapp = {
    node_id: undefined,
    functions: [],
    has_no_name: false,
    data: {},
    dict: {},
    tmpl: {},
    tree_data: [],

    saveTree: function () {
        let tree = xapp.transform($tree.tree('getTree'));
        if (xapp.has_no_name) {
            tree = tree.Properties;
        }
        let json = JSON.stringify(tree);
        $.ajax({
            type: "POST",
            url: 'saveTree?file=' + file,
            data: json,
            dataType: "json",
            contentType: "application/json; charset=utf-8",
            success: function (data) {
                if (data.status == 'ok') {
                    //let node = $('#tree').tree('getNodeById', xapp.node_id);
                    //	$('#tree').tree('updateNode', node, xapp.form.name);
                    setMsg('saved');
                    return true;
                } else {
                    setMsg(data.msg, 'danger');
                    return false;
                }
            }
        });
    },
    convert_data: function (d) {
        if (d == '') return d;

        if (d === "false") {
            return false;
        } else if (d === "true") {
            return true;
        }

        let n = +d;
        if (!isNaN(n)) {
            return n;
        }

        return d;
    },

    updateTree: function () {
        let key = $('#key').val();
        let node = $tree.tree('getNodeById', key);
        if (!node) return;
        let name = $('#name').val();
        let oldname = $('#name').attr('data-old');
        $('#fieldset textarea.form-control').each(function (index) {
            let isdisabled = $(this).attr('disabled');
            if (isdisabled !== "disabled") {
                const v = $(this).val().split("\n");
                const n = $(this).attr('name');
                node.properties[n] = xapp.convert_data(v);
            }
        });

        $('#fieldset input.form-control').each(function (index) {
            let isdisabled = $(this).attr('disabled');
            if (isdisabled !== "disabled") {
                const v = $(this).val();
                const n = $(this).attr('name');
                node.properties[n] = xapp.convert_data(v);
            }
        });

        $('.selectpicker').each(function () {
            var v = $(this).val();
            var n = $(this).attr('name');
            node.properties[n] = xapp.convert_data(v);
        });

        $('.bsmultiselect').each(function () {
            var v = $(this).val();
            var n = $(this).attr('name');
            node.properties[n] = xapp.convert_data(v);
        });


        if (oldname != name && name.trim() !== '') {
            $tree.tree('updateNode', node, name);
        }
    },


    setHeight: function (me) {
        me.style.height = '30px';
        let height = me.scrollHeight < 40 ? 40 : me.scrollHeight;
        me.style.height = height + 'px';
    },

    renderTree(key, d) {
        $('#logic').show();
        $('#logic_select').hide();
        $('#logic_input').hide();
        $('#logic_rm').css("visibility", "hidden");
        let add_drop = $('#add_drop');
        $('#add_drop li a.entity').remove();
        $('#add_drop li a.task').remove();
        var selectedNode = $tree.tree('getSelectedNode');
        if (selectedNode.name == 'success') {
            let siblings = selectedNode.parent.children;
            let list = [];
            for (let i = 0; i < siblings.length; ++i) {
                let s = siblings[i];
                if ('entity_groups' == s.name) {
                    list = Object.keys(s.properties);
                    break;
                }
            }

            for (let i = 0; i < list.length; ++i) {
                add_drop.append('<li><a href="#" class="entity ">' + list[i] + '</a></li>');
            }

            let uncles = selectedNode.parent.parent.children;
            for (let i = 0; i < uncles.length; ++i) {
                let name = uncles[i].name;
                add_drop.append('<li><a href="#" class="task ">' + name + '</a></li>');

            }
        }

        let data = {};
        let keys = Object.keys(d);
        if (keys[0] == 0) {
            d = Object.values(d);
        } else if (keys.length === 0) {
            d = [];
        } else {
            if (d.value && d.value == "object") {
                d = [];
            } else {
                d = [d];
            }
        }

        //d is an array of object
        data[key] = d;
        let treedata = xapp.transformObjectData(data);
        $objecttree = $('#objecttree').tree({
            dragAndDrop: false,
            openedIcon: '&#9663;',
            closedIcon: '&#9657;',
            autoOpen: 1,
            data: [treedata]
        });

        $objecttree.on(
            'tree.select',
            function (event) {
                let node = event.node;
                if (node) {
                    $('#logic_rm').css("visibility", "visible");
                    let mainnode = $tree.tree('getSelectedNode');
                    if (mainnode.name == 'success') {
                        $('#logic_input').hide();
                        if (['success'].includes(node.name)) {
                            $('#logic_select').show();
                            $('#logic_select .entity').hide();
                            $('#logic_select .task').hide();
                            $('#logic_select .action').hide();
                            $('#logic_select .logic').show();
                        } else if (['AND', 'OR'].includes(node.name)) {
                            $('#logic_select').show();
                            $('#logic_select .entity').hide();
                            $('#logic_select .task').hide();
                            $('#logic_select .action').show();
                            $('#logic_select .logic').show();
                        } else if (['API', 'INFORM', 'INSERT', 'SIMPLE', 'QUERY', 'UPDATE', 'VERIFY'].includes(node.name)) {
                            $('#logic_select').show();
                            $('#logic_select .logic').hide();
                            $('#logic_select .action').hide();
                            $('#logic_select .entity').show();
                            $('#logic_select .task').hide();
                        } else if ('TASK' == node.name) {
                            $('#logic_select').show();
                            $('#logic_select .logic').hide();
                            $('#logic_select .entity').hide();
                            $('#logic_select .action').hide();
                            $('#logic_select .task').show();
                        } else {
                            $('#logic_select').hide();
                        }
                    } else {
                        $('#logic_input').show();
                    }
                }
            }
        );
	$('#add_drop a').off('click');
        $('#add_drop a').on('click', function (e) {
            e.stopPropagation();
            let node = $objecttree.tree('getSelectedNode');
            let mainnode = $tree.tree('getSelectedNode');
            if (!node) return false;
            let name = $(e.target).html();
            let id = ID();
            let data = {id: id, name: name, children: []};
            $objecttree.tree('appendNode', data, node);
            const n = $objecttree.tree('getNodeById', id);
            $objecttree.tree('selectNode', n);
            let root = $objecttree.tree('getTree');
            let treedata = xapp.transformObjectTree(root.children[0]);
            mainnode.properties = treedata['success'][0];
        });

	$('#logic_rm').off('click');
        $('#logic_rm').on('click', function () {
            let node = $objecttree.tree('getSelectedNode');
            let mainnode = $tree.tree('getSelectedNode');
            if (!node) return false;
            $objecttree.tree('removeNode', node);
            let root = $objecttree.tree('getTree');
            if (mainnode.name == 'success') {
                let treedata = xapp.transformObjectTree(root.children[0]);
                mainnode.properties = treedata['success'][0];
            } else {
                let treedata = xapp.transformLogicTree(root.children[0]);
                mainnode.properties['Logic'] = treedata['Logic'];
            }
        });

	$('#logic_input_add').off('click');
        $('#logic_input_add').on('click', function () {
            let name = $('#logic_input_text').val();
            if (name == '') return;
            $('#logic_input_text').val('');
            let node = $objecttree.tree('getSelectedNode');
            let mainnode = $tree.tree('getSelectedNode');
            if (!node) return false;
            let id = ID();
            let data = {id: id, name: name, children: []};
            $objecttree.tree('appendNode', data, node);
            const n = $objecttree.tree('getNodeById', id);
            $objecttree.tree('selectNode', n);
            let root = $objecttree.tree('getTree');
            let treedata = xapp.transformLogicTree(root.children[0]);
            mainnode.properties['Logic'] = treedata['Logic'];
        });
    },
    renderTip: function (path, property, html) {
        let tip = tooltips.hasOwnProperty(path) ? (tooltips[path].hasOwnProperty(property) ? tooltips[path][property] : false) : false;
        if (tip) {
            let info_template = document.querySelector('#info_template');
            let info_clone = info_template.content.cloneNode(true);
            let tooltip = $(info_clone).find('.tip');
            tooltip.html(tip);
            let label = $(html).find('label');
            $(info_clone).appendTo(label);
        }
    },
    renderForm: function (node) {
        this.reset();
        if (node == undefined) return;

        if (node.name === '_name_') {
            $('#name').val("");
        } else {
            $('#name').val(node.name);
        }

        $('#name').attr('data-old', node.name);
        $('#key').val(node.id);
        $('#logic').hide();
        $('#objecttree').tree('destroy');
        let tmpl = xapp.dict[node.id];
        let path = JSON.stringify(tmpl.path);
        $('#node_name .info').remove();
        this.renderTip(path, 'name', $('#node_name'));
        $('#newinputbtn').hide();

        if (tmpl.name !== '_name_') {
            $('#name').hide();
            $('#node_name label').hide();
            //$('#name').attr('readonly', true);
            $('#deletebtn').hide();
        } else {
            $('#name').show();
            $('#node_name label').show();
            //$('#name').attr('readonly', false);
            $('#deletebtn').show();
        }

        if (tmpl && tmpl.properties.value && tmpl.properties.value == 'object') {
            xapp.renderTree(node.name, node.properties);
            this.hover_tip();
            return;
        }

        if (path == '["Entity","_name_","methods"]' || path == '["Task","_name_","entities","_name_","methods"]') {
            $('#newinputbtn').show();
            for (let method in node.properties) {
                let d = node.properties.hasOwnProperty(method) ? node.properties[method] : '';
                let t = tmpl.properties.hasOwnProperty(method) ? tmpl.properties[method] : '';
                let html;
                if (node.properties[method] !== undefined) {
                    if (Array.isArray(t)) {
                        d = Array.isArray(d) ? d.join("\n") : d;
                        html = $.tmpl('textarea', [{id: method, value: d}]);
                    } else {
                        html = $.tmpl('text', [{id: method, value: d}]);
                    }
                }
                if (html !== undefined) {
                    this.renderTip(path, method, html);
                    html.appendTo(fieldset);
                }
            }
        }
        else {
            for (let i in tmpl.properties) {
                let d = node.properties.hasOwnProperty(i) ? node.properties[i] : '';
                let t = tmpl.properties.hasOwnProperty(i) ? tmpl.properties[i] : '';

                let html;
                if (i == '_name_' || i == '_property_') {
                    $('#newinputbtn').show();
                    for (let j in node.properties) {
                        let dd = node.properties.hasOwnProperty(j) ? node.properties[j] : '';
                        if (t == 'multiselect') {

                            let options = [];
                            if (path == '["Task","_name_","entity_groups"]') {
                                let task = node.parent;
                                let entities;
                                node.parent.children.forEach(function (p) {
                                    if (p.name == 'entities') {
                                        entities = p.children;
                                    }
                                });
                                entities.forEach(function (entity) {
                                    options.push(entity.name);
                                });
                            }
                            html = $.tmpl('multiselect', [{id: j, select: options}]);
                            dd = Array.isArray(dd) ? dd : [dd];
                            $.each(dd, function (i, e) {
                                $(html).find("option[value='" + e + "']").prop("selected", true);
                            });
                        } else if (Array.isArray(dd)) {
                            html = $.tmpl('textarea', [{id: j, value: dd.join("\n")}]);
                        } else {
                            html = $.tmpl('text', [{id: j, value: dd}]);
                        }
                        html.appendTo(fieldset);
                    }
                    $('#typeform #fieldset label').hover(
                        function (e) {
                            let template = document.querySelector('#rename_template');
                            let clone = template.content.cloneNode(true);
                            $(this).append(clone);
                            $('img.delete').click(function (e) {
                                let t = $(e.target).closest('label');
                                if (t) {
                                    let id = t.attr('for');
                                    node = $tree.tree('getNodeById', xapp.node_id);
                                    delete node.properties[id];
                                    t.parent().remove();
                                }
                            });
                            let handleRename = function (e) {
                                let new_key = $('#rename_input').val();
                                if (new_key) {
                                    let t = $(e.target).closest('label');
                                    if (t) {
                                        let old_key = t.attr('for');
                                        let node = $tree.tree('getNodeById', xapp.node_id);

                                        if (old_key !== new_key) {
                                            Object.defineProperty(node.properties, new_key, Object.getOwnPropertyDescriptor(node.properties, old_key));
                                            delete node.properties[old_key];
                                            xapp.renderForm(node);
                                        }

                                        t.find('span').html(new_key);
                                    }
                                    $('.rename-control').remove();
                                }
                            };
                            $('#rename_btn').click(handleRename);
                            $('#rename_input').on('keypress', function (e) {
                                if (e.which == 13) {
                                    handleRename(e);
                                }
                            });
                        },
                        function (e) {
                            $('.rename-control').remove();
                        });
                    continue;
                } else if (Array.isArray(t)) {
                    if (t == 'object') {
                        xapp.renderTree(i, d);
                    } else {
                        d = Array.isArray(d) ? d.join("\n") : d;
                        html = $.tmpl('textarea', [{id: i, value: d}]);
                    }
                } else if (typeof (t) == 'string' && t.includes('|')) {
                    let options = t.split('|');
                    html = $.tmpl('select', [{id: i, options: options, value: d}]);
                    let v = typeof (d) == 'boolean' ? d.toString() : d;
                    $(html).find('select').val(v);
                } else if (typeof (t) == 'string' && t == 'datalist') {
                    html = $.tmpl('datalist', [{id: i, options: xapp.functions, value: d}]);
                } else {
                    html = $.tmpl('text', [{id: i, value: d}]);
                }

                if (html !== undefined) {
                    this.renderTip(path, i, html);
                    html.appendTo(fieldset);
                }
            }
        }
        $('textarea').each(function () {
            xapp.setHeight(this);
        });
        $('.selectpicker').selectpicker();
        $('.bsmultiselect').multiselect({numberDisplayed: 6});

        if (path == '["Task","_name_"]') {
            xapp.toggleRepeat_repsonse();
            $('#repeat').change(function () {
                xapp.toggleRepeat_repsonse();
            });
        }

        if (path == '["Entity","_name_"]' || path == '["Task","_name_","entities","_name_"]') {
            xapp.toggleSuggest_value();
            $('#type').change(function () {
                xapp.toggleSuggest_value();
            });
        }

        if (tmpl.children.length > 0 && tmpl.children[0].name == '_name_') {
            $('#new').html('New ' + node.name);
            $('#new').attr('data-id', node.id);
            $('#new').show();
        } else {
            $('#new').hide();
        }

        this.hover_tip();
    },

    hover_tip: function () {
        $('.info').hover(function () {
            let tooltip = $(this).find('.tip');
            $(tooltip).show();
        }, function () {
            let tooltip = $(this).find('.tip');
            $(tooltip).hide();
        });

    },

    toggleRepeat_repsonse: function () {
        if ($('#repeat').val() == 'true') {
            $('#repeat_response').parent().show();
            $('#repeat_response').attr('disabled', false);
        } else {
            $('#repeat_response').parent().hide();
            $('#repeat_response').attr('disabled', true);
        }
    },

    toggleSuggest_value: function () {
        if ($('#type').val() == 'PICKLIST') {
            $('#suggest_value').parent().parent().show();
            $('#suggest_value').attr('disabled', false);
        } else {
            $('#suggest_value').parent().parent().hide();
            $('#suggest_value').attr('disabled', true);
        }
    },


    reset: function () {
        $('#fieldset').empty();
    },

    transformObjectTree: function (node) {
        let children = node.children;
        let name = node.name;
        if (!['success', 'AND', 'OR', 'TASK', 'API', 'INFORM', 'INSERT', 'SIMPLE', 'QUERY', 'UPDATE', 'VERIFY'].includes(name)) {
            return name;
        }
        let obj = {};
        obj[name] = [];
        for (let i = 0; i < children.length; ++i) {
            let kid = children[i];
            obj[name].push(xapp.transformObjectTree(kid));
        }

        return obj;
    },


    transformLogicTree: function (node) {
        let children = node.children;
        let name = node.name;
        let obj = {};
        obj[name] = [];
        let l = children.length;
        if (l == 0) return name;
        for (let i = 0; i < l; ++i) {
            let kid = children[i];
            obj[name].push(xapp.transformLogicTree(kid));
        }

        return obj;
    },

    transform: function (node) {
        let children = node.children;
        let obj = node.properties ? copy(node.properties) : {};
        for (let i = 0; i < children.length; ++i) {
            let o = children[i];
            let name = o.name;
            let kids = o.children;
            let oo = copy(o.properties);
            for (let j = 0; j < kids.length; ++j) {
                let kid = kids[j];
                oo[kid.name] = xapp.transform(kid);
            }
            obj[name] = oo;
        }

        return obj;
    },

    transformObjectData: function (data) {
        let obj = {'children': []};
        if (typeof data == 'string') {
            obj['name'] = data;
            obj['id'] = ID();
            return obj;
        }

        for (const [key, value] of Object.entries(data)) {
            //console.log(`${key}: ${value}`);
            obj['name'] = key;
            obj['id'] = ID();
            for (let i = 0; i < value.length; ++i) {
                let kid = xapp.transformObjectData(value[i]);
                obj['children'].push(kid);
            }
        }
        return obj;
    },

    transformTempData: function (data, p) {
        let obj = {'children': [], 'properties': {}};
        for (const prop in data) {
            const value = data[prop];
            if (value && !Array.isArray(value) && typeof value === 'object') {
                let path = copy(p);
                path.push(prop);
                let kid = xapp.transformTempData(value, path);
                let id = ID();
                kid["id"] = id;
                kid["name"] = prop;
                kid["path"] = path;
                obj.children.push(kid);
            } else if (value === 'object') {
                let path = copy(p);
                path.push(prop);
                let kid = {}
                let id = ID();
                kid["id"] = id;
                kid["name"] = prop;
                kid["path"] = path;
                kid["properties"] = {value};
                obj.children.push(kid);
            } else {
                obj.properties[prop] = value;
            }
        }
        return obj;
    },

    transformData: function (data, p) {
        let obj = {'children': [], 'properties': {}};
        for (const prop in data) {
            const value = data[prop];
            let path = copy(p);
            path.push(prop);
            let tmpl = xapp.findTmpl(path);
            if (value && !Array.isArray(value) && typeof value === 'object' && tmpl) {
                const id = ID();
                let kid = xapp.transformData(value, path);
                kid["id"] = id;
                kid["name"] = prop;
                kid["path"] = path;
                obj.children.push(kid);
                xapp.dict[id] = tmpl;
            } else {
                obj.properties[prop] = value;
            }
        }
        return obj;
    },

    findTmpl: function (path) {
        var node = $tmpltree.tree('getNodeByCallback',
            function (node) {
                if (node.path === path) return true;
                if (node.path == null || path == null) return false;
                if (node.path.length !== path.length) return false;
                for (var i = 0; i < path.length; ++i) {
                    if (node.path[i] !== path[i] && node.path[i] != '_name_') {
                        return false;
                    }
                }
                return true;
            }
        );
        return node;
    },

    findTree: function (path) {
        var node = $tree.tree('getNodeByCallback',
            function (node) {
                if (node.path === path) return true;
                if (node.path == null || path == null) return false;
                if (node.path.length !== path.length) return false;
                for (var i = 0; i < path.length; ++i) {
                    if (node.path[i] !== path[i] && path[i] != '_name_') {
                        return false;
                    }
                }
                return true;
            }
        );
        return node;
    },


    getSibling: function (node) {
        if (!node) return false;
        if (!node.parent) return false;
        let sibling = node.parent.children;
        for (let i = 0; i < sibling.length; ++i) {
            if (sibling[i].id == node.id) {
                if (i + 1 == sibling.length) {
                    return false;
                } else {
                    return sibling[i + 1];
                }
            }
        }
        return false;
    },

    getKid: function (node) {
        if (!node) return false;
        if (node.children.length > 0) {
            return node.children[0];
        }
        return false;
    },

    loadCreate: function (move, tmpl, node, parent) {
        if (tmpl) {
            if (node) {
                $tree.tree('selectNode', node);
                return {move: move, tmpl: tmpl, next: node};
            } else {
                let name = tmpl.name;
                let head = 'Create new ' + name;
                let question = ''
                if (name == '_name_') {
                    name = tmpl.parent.name;
                    head = 'Create one new ' + name;
                }
                else if (name == 'entities') {
                    question = 'Do you want to create a new entity?';
                }
                else if (name == 'methods') {
                    question = 'Do you want to create entity extraction methods for this entity?';
                }
                else  if (name == 'success') {
                    question = 'Do you want to create the And-or task tree structure?';
                }
                else {
                    question = 'Do you want to create new ' + name + '?'
                }
                choice(head, question, 'Yes', 'No',
                    function () {
                        xapp.create(move, tmpl, parent);
                    },
                    function () {
                        xapp.wizard(move);
                    });

                return true;
            }
        }

        if (node) {
            $tree.tree('selectNode', node);
            return {move: move, tmpl: tmpl, next: node};
        }

        return false;
    },

    wizard: function (move) {

        let parent = $tree.tree('getSelectedNode');
        let r, tmpl, node;
        if (!parent) {
            tmpl = $tmpltree.tree('getTree').children[0];
            parent = $tree.tree('getTree'); //root
        } else {
            tmpl = xapp.getKid(xapp.dict[parent.id]);
        }
        node = xapp.getKid(parent);

        if (move !== 'kid') {
            r = xapp.loadCreate('kid', tmpl, node, parent);
            if (r) return r;
        }

        tmpl = xapp.getSibling(xapp.dict[parent.id]);
        node = xapp.getSibling(parent);
        r = xapp.loadCreate('sibling', tmpl, node, parent);
        if (r) return r;

        tmpl = xapp.dict[parent.id] ? xapp.getSibling(xapp.dict[parent.id].parent) : false;
        node = xapp.getSibling(parent.parent);
        r = xapp.loadCreate('uncle', tmpl, node, parent);
        if (r) return r;

        tmpl = xapp.dict[parent.parent.id] ? xapp.getSibling(xapp.dict[parent.id].parent.parent) : false;
        node = xapp.getSibling(parent.parent.parent);
        r = xapp.loadCreate('grandparent', tmpl, node, parent);
        if (r) return r;

        return false;

    },

    create: function (move, tmpl, node) {
        //console.log('create', move);
        xapp.node_id = ID();
        let name = tmpl.name;
        xapp.dict[xapp.node_id] = tmpl;
        let next_data = {id: xapp.node_id, name: name, children: [], properties: {}};
        if (move == 'kid') {
            $tree.tree('appendNode', next_data, node);
        } else if (move == 'sibling') {
            $tree.tree('appendNode', next_data, node.parent);
        } else if (move == 'uncle') {
            $tree.tree('appendNode', next_data, node.parent.parent);
        } else if (move == 'grandparent') {
            $tree.tree('appendNode', next_data, node.parent.parent.parent);
        }

        next = $tree.tree('getNodeById', xapp.node_id);
        $tree.tree('selectNode', next);
        return {move: move, tmpl: tmpl, next: next};
    },

};


let $tree;
let $tmpltree;
$(document).ready(function () {

    $('#saveall').hide();
    $('#new').hide();

    $.ajax({
        url: '/tree?file=' + file + '&ts=' + ts,
        success: function (rsp) {
            if (rsp.status == 'ok') {
                xapp.tmpl = rsp.tmpl;
                xapp.tmpl_transformed = xapp.transformTempData(xapp.tmpl, [], []);
                let tmpltree_data;

                if (jQuery.isEmptyObject(xapp.tmpl_transformed.properties)) {
                    tmpltree_data = xapp.tmpl_transformed['children'];
                } else {
                    xapp.tmpl_transformed['name'] = 'template';
                    xapp.tmpl_transformed['id'] = ID();
                    xapp.tmpl_transformed['path'] = [''];
                    tmpltree_data = [xapp.tmpl_transformed];
                }

                $tmpltree = $('#tmpltree').tree({
                    dragAndDrop: false,
                    autoOpen: 0,
                    data: tmpltree_data
                });


                xapp.data = rsp.data;
                xapp.data_transformed = xapp.transformData(xapp.data, [], []);

                let tree_data;
                if (jQuery.isEmptyObject(xapp.data_transformed.properties)) {
                    tree_data = xapp.data_transformed['children'];
                } else {
                    let id = ID();
                    xapp.data_transformed['id'] = id;
                    xapp.data_transformed['name'] = 'Properties';
                    let tmpl = xapp.findTmpl(['']);
                    xapp.dict[id] = tmpl;
                    tree_data = [xapp.data_transformed];
                    xapp.has_no_name = true;
                }

                $tree = $('#tree').tree({
                    dragAndDrop: false,
                    openedIcon: '&#9663;',
                    closedIcon: '&#9657;',
                    autoOpen: 0,
                    data: tree_data
                });
                init_tree();

                xapp.functions = rsp.functions;

                $('#dlbtn').attr('href', '/' + rsp.file);

                let history = rsp.history.sort().reverse();
                for (let i = 0; i < history.length; i++) {
                    let filename = history[i];
                    let l = filename.length;
                    $('#history').append("<option >" + filename.substring(l - 22, l) + "</option>");
                }
                if (['entity', 'task'].includes(file)) {
                    $('#history').append("<option >reset</option>");
                }
            } else {
                if (rsp.msg != 'Node not found') {
                    setMsg(rsp.msg, 'danger');
                }
            }
        }
    });

    function init_tree() {

        $tree.on('tree.init', function () {
        });

        $tree.on(
            'tree.select',
            function (event) {
                xapp.updateTree();
                $('#typeform').show();
                let node = event.node;
                if (node) {
                    xapp.node_id = node.id;
                    xapp.renderForm(node);
                    $('#next').show();
                    $('#saveall').hide()
                }
            }
        );

        $tree.on(
            'tree.move',
            function (event) {
                event.preventDefault();
                let name = event.move_info.moved_node.name;
                let node = event.move_info.moved_node;
                let parent = event.move_info.previous_parent;
                let target = event.move_info.target_node;

                //  event.move_info.position
                if (confirm('Confirm move ' + name + ' from ' + parent.name + ' to ' + target.name + '?')) {
                    let id = node.id;
                    let pid = parent.id;
                    let tid = target.id;
                    event.move_info.do_move();
                    xapp.saveTree();

                }
            }
        );

        xapp.wizard();
    }

    $('#inputform').on('submit', function (e) {
        let t = e.target;
        let name = $('#inputname').val();
        let node = $tree.tree('getNodeById', xapp.node_id);
        let tmpl = xapp.dict[node.id];
        let path = JSON.stringify(tmpl.path);
        if (path == '["Task","_name_","entities","_name_","methods"]') {
            name = $('#inputlist').val();
            if (name == 'user_utterance') {
                node.properties = {};
            } else {
                if ('user_utterance' in node.properties) {
                    node.properties = {};
                }
            }
        }

        let oldname = $('#inputname').attr('data-old');
        let type = $('#inputselect').val();
        let oldtype = $('#inputselect').attr('data-old');

        if (!name || name === oldname && type === oldtype) return;

        $('#fieldset').empty();
        let value = type == 'text' ? '' : [''];

        if (!oldname) {
            node.properties[name] = value;
        } else {
            value = node.properties[oldname];
            if (name !== oldname) {
                delete node.properties[oldname];
            }
            if (type !== oldtype) {
                if (type == 'text') {
                    value = value.join(' ');
                } else {
                    value = [value];
                }
            }
            node.properties[name] = value;
        }

        xapp.renderForm(node);
        $('textarea').each(function () {
            xapp.setHeight(this);
        });
        e.preventDefault();
        $('#fieldModal').modal('hide');
    });

    $('#newinputbtn').on('click', function (e) {
        $('#inputform')[0].reset();
        $('#fieldModal').modal('show');
        let node = $tree.tree('getNodeById', xapp.node_id);
        let tmpl = xapp.dict[node.id];
        let path = JSON.stringify(tmpl.path);
        if (path == '["Task","_name_","entities","_name_","methods"]') {
            $('#inputname').hide();
            $('#inputlist').show();
            $('#inputselect option[value=text]').show();
            $('#inputselect option[value=textarea]').show();
            $('#inputselect option[value=multiselect]').hide();
        } else if (path == '["Task","_name_","entity_groups"]') {
            $('#inputname').show();
            $('#inputlist').hide();
            $('#inputselect option[value=text]').hide();
            $('#inputselect option[value=textarea]').hide();
            $('#inputselect option[value=multiselect]').show();
            $('#inputselect').val('multiselect');
        } else if (path == '["Response","_name_"]' || path == '["Response"]') {
            $('#inputname').show();
            $('#inputlist').hide();
            $('#inputselect option[value=text]').hide();
            $('#inputselect option[value=textarea]').show();
            $('#inputselect').val('textarea');
            $('#inputselect option[value=multiselect]').hide();
        } else {
            $('#inputname').show();
            $('#inputlist').hide();
            $('#inputselect option[value=text]').show();
            $('#inputselect option[value=textarea]').show();
            $('#inputselect option[value=multiselect]').show();
        }
    });


    $('#savebtn').click(function (e) {
        e.preventDefault();
        xapp.updateTree();
        xapp.saveTree();
    });

    $('#newbtn').click(function (e) {
        let sLabel = window.prompt("Enter a name for the new node ", "");

        if (sLabel && sLabel.length > 0) {
            let parent_node = $tree.tree('getNodeById', xapp.node_id);
            let key = ID();
            let parameter = {placeholder: ''};
            let node = {id: key, name: sLabel, children: [], properties: parameter};
            $tree.tree('appendNode', node, parent_node);

            xapp.saveTree();
        }
    });

    $('#deletebtn').click(function (e) {
        choice('Please Confirm', 'Delete this node?', 'OK', 'Cancel', function () {
            let node = $tree.tree('getNodeById', xapp.node_id);
            let name = node.name;
            let parent_id = node.parent.id;
            let parent = $tree.tree('getNodeById', parent_id);
            delete parent.properties[name];
            $tree.tree('removeNode', node);
            xapp.saveTree();
        });
    });

    $('#duplicatebtn').click(function (e) {
        choice('Please Confirm', 'Duplicate this node?', 'OK', 'Cancel', function () {
            let node = $tree.tree('getNodeById', xapp.node_id);
            let key = ID();
            let name = node.name + ' Copy';
            let parameter = copy(node.properties);
            let newnode = {id: key, name: name, children: [], properties: parameter};

            let parent_id = node.parent.id;
            let parent = $tree.tree('getNodeById', parent_id);

            $tree.tree('appendNode', newnode, parent);

            xapp.saveTree();

        });
    });


    $('#dlbtn').click(function (e) {
        e.preventDefault();
        let url = "/static/yamls/" + $(this).attr('href').split("/").pop() + '?v=' + ID();
        // let url = $(this).attr('href') + "?v=" + ID();
        window.open(url, '_blank');
    });

    $('#ulbtn').click(function (e) {
        e.preventDefault();
        let filetype = $('#file').val();
        $('#filetype').html(filetype);
        $('#uploadModal').modal('show');
    });


    $('#inputlist').change(function (e) {
        if ($(this).val() == 'fuzzy_matching') {
            $('#inputselect').val('textarea');
        } else {
            $('#inputselect').val('text');
        }
    });

    $('#uploadform').submit(function (e) {
        e.preventDefault();
        let files = $("#uploadfile")[0].files;
        if (files.length == 0) return;
        let url = $("#uploadform").attr('action');
        var fd = new FormData();
        fd.append('file', files[0]);
        fd.append('type', file);
        $('#uploadModal').modal('hide');

        $.ajax({
            url: url,
            type: 'POST',
            data: fd,
            success: function (data) {
                if (data.status == "ok") {
                    setMsg('uploaded');
                } else {
                    setMsg(data.msg, 'danger');
                }
            },
            cache: false,
            contentType: false,
            processData: false
        });
    });

    $("#menu-toggle").click(function (e) {
        e.preventDefault();
        $("#wrapper").toggleClass("toggled");
        if ($('#wrapper').hasClass('toggled')) {
            $('#menu-toggle').html('⧈');
            if (window_width < 480) {
                $('#logoutbtn,#user_id,#duplicatebtn,#deletebtn').fadeIn(800);
                $('#search_input').hide();
            }
        } else {
            $('#menu-toggle').html('⧉');
            if (window_width < 480) {
                $('#logoutbtn,#user_id,#duplicatebtn,#deletebtn').hide();
                $('#search_input').fadeIn(800);
            }
        }
    });


    $('#new').click(function (e) {
        let node_id = $(this).attr('data-id');
        let node = $tree.tree('getNodeById', node_id);
        let tmpl = xapp.dict[node_id].children[0];
        xapp.create('kid', tmpl, node);
    });

    $('#next').click(function (e) {
        xapp.updateTree();
//		xapp.saveTree();
        xapp.wizard();
    });


    if (!file) {
        file = 'task';
    }

    $('#file').val(file);
    $('#file').on('change', function () {
        let f = $(this).val();
        window.location.href = '/?file=' + f;
    });

    $('#history').on('change', function () {
        let h = $(this).val();
        window.location.href = '/?file=' + file + '&ts=' + h;
    });


    window.history.pushState({"html": "", "pageTitle": ""}, "", "/?file=" + file);

});
