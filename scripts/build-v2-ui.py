"""Extend the existing resource pack without losing v1 mod translations."""
from pathlib import Path
import json,zipfile
ROOT=Path(__file__).resolve().parents[1]
labels={
 'task.heracles.progress.desc.incomplete.singular':'Falta %s objetivo',
 'task.heracles.progress.desc.incomplete.plural':'Faltan %s objetivos',
 'task.heracles.progress.desc.complete':'Objetivos completados',
 'task.heracles.check.title.singular':'Confirmación de lectura',
 'task.heracles.check.desc.singular':'Marcá la casilla cuando termines esta práctica',
 'task.heracles.require_quest.title':'Completar otra misión',
 'task.heracles.require_quest.desc':'Completá «%s»',
 'task.heracles.item.title.singular':'Conseguir: %s',
 'task.heracles.item.title.plural':'Entregar: %s',
 'task.heracles.item.title.item':'Conseguir: %s',
 'task.heracles.item.title.tag':'Conseguir cualquiera de: %s',
 'task.heracles.item.desc.item':'Conseguí %s × %s',
 'task.heracles.item.desc.tag':'Conseguí %s de cualquier %s',
 'task.heracles.item.submit.title.item':'Entregar: %s',
 'task.heracles.item.submit.title.tag':'Entregar cualquiera de: %s',
 'task.heracles.item.submit.desc.item':'Entregá %s × %s',
 'task.heracles.item.submit.desc.tag':'Entregá %s de cualquier %s',
 'task.heracles.item.submit.button.tooltip':'Consume %s objetos',
 'task.heracles.advancement.title.singular':'Completar un logro',
 'task.heracles.advancement.title.plural':'Completar un logro',
 'task.heracles.advancement.desc.singular':'Completá «%s»',
 'task.heracles.advancement.desc.plural':'%s Completá uno de estos logros',
 'task.heracles.changed_dimension.title.singular':'Viajar entre dimensiones',
 'task.heracles.changed_dimension.desc.singular':'Desde %s hasta %s',
 'task.heracles.kill_entity.title.singular':'Derrotar: %s',
 'task.heracles.kill_entity.title.plural':'Derrotar: %s',
 'task.heracles.kill_entity.desc.singular':'Derrotá %s × %s',
 'task.heracles.kill_entity.desc.plural':'Derrotá %s × %s',
 'task.heracles.composite.title.singular':'Completá uno de los objetivos',
 'task.heracles.composite.title.plural':'Completá %s objetivos',
}
source=ROOT/'pack/client-overrides/resourcepacks/Virgos-MC-UI.zip'
with zipfile.ZipFile(source) as z:entries={name:z.read(name) for name in z.namelist()}
for lang in ['es_ar','es_es','es_mx','es_cl','es_uy','es_ve']:
    key=f'assets/heracles_tasks/lang/{lang}.json';current=json.loads(entries.get(key,b'{}'));current.update(labels);entries[key]=json.dumps(current,ensure_ascii=False).encode('utf-8')
target=ROOT/'.lab/v2/client-overrides/resourcepacks/Virgos-MC-UI.zip';target.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
    for name,content in entries.items():z.writestr(name,content)
print('Existing resource pack preserved;',len(labels),'task labels translated for six Spanish locales.')
