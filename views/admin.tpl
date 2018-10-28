% rebase('base.tpl', title='Short')
% for db_name, items in sorted(results):
<h2>{{ db_name }}</h2>
<ul>
%for item in sorted(items, key=itemgetter('alias')):
<li><a href="{{ item['url']}}">{{item['alias']}} - {{item['url']}}</a></li>
% end
</ul>
% end
