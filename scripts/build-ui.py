"""Pack-owned Spanish UI labels, with no upstream textures or game binaries."""
from pathlib import Path
import json
import zipfile
import argparse

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--staging-only',action='store_true',help='Leave the running QA client resources untouched')
args=parser.parse_args()
labels={
 'rewards.heracles.toast':'Recompensas recibidas',
 'quest.heracles.in_progress':'En progreso','quest.heracles.completed':'Completada',
 'quest.heracles.completed_claimed':'Reclamada','quest.heracles.dependencies':'Requisitos',
 'quest.heracles.locked':'Bloqueada','quest.heracles.available':'Disponible','quest.heracles.claimed':'Reclamada',
 'quest.heracles.toast':'¡Misión completada!','quest.heracles.toast.desc':'Presioná [%s] para abrir',
 'quest_unlocked.heracles.toast':'¡Nueva misión!','quest_unlocked.heracles.toast.desc':'Presioná [%s] para abrir',
 'quest.heracles.tutorial.title':'Tu códice de aventuras','quest.heracles.tutorial.desc':'Presioná [%s] para abrir',
 'item.heracles.quest_book':'Códice de aventuras','key.heracles.open_quests':'Abrir códice',
 'gui.heracles.pinned_quests':'Misiones fijadas','gui.heracles.pinned_quests.move':'Mover misiones fijadas',
 'gui.heracles.pinned_quests.placeholder':'Misión %s',
 'gui.heracles.progress.title.incomplete':'Pendiente','gui.heracles.progress.title.complete':'Completada',
 'gui.heracles.progress.desc.incomplete.singular':'Falta %s objetivo',
 'gui.heracles.progress.desc.incomplete.plural':'Faltan %s objetivos',
 'gui.heracles.progress.desc.complete.singular':'Queda %s recompensa',
 'gui.heracles.progress.desc.complete.plural':'Quedan %s recompensas',
 'gui.heracles.progress.desc.complete_claimed':'Recompensas recibidas',
 'gui.heracles.rewards.title':'Recompensas','gui.heracles.rewards.status':'Estado de recompensas',
 'gui.heracles.rewards.select_claim':'Reclamar esta recompensa','gui.heracles.rewards.claim':'Reclamar recompensas',
 'gui.heracles.rewards.claim_reward':'Reclamar','gui.heracles.tasks.title':'Objetivos',
 'gui.heracles.tasks.progress':'Progreso de objetivos','gui.heracles.tasks.collection_type.automatic':'Conseguir',
 'gui.heracles.tasks.collection_type.manual':'Entregar','gui.heracles.tasks.collection_type.consume':'Entregar automáticamente',
 'gui.heracles.tasks.check':'Completar objetivo','gui.heracles.tasks.submit':'Entregar objetos',
 'gui.heracles.tasks.submit.xp':'Entregar experiencia','gui.heracles.quests.view':'Ver misiones',
 'gui.heracles.quests.overview':'Descripción','gui.heracles.quests.claimable':'Recompensas pendientes',
 'gui.heracles.group.groups':'Capítulos','gui.heracles.save':'Guardar','gui.heracles.close':'Cerrar',
 'gui.heracles.submit':'Enviar','gui.heracles.confirm':'Confirmar','gui.heracles.search':'Buscar',
 'gui.heracles.error.quests.load_fail':'No se pudieron cargar las misiones. Revisá el registro.',
 'rei.heracles.heracles.tooltip':'Abrir códice',
}
claims={
 'gui.xaero_pac_back':'Volver',
 'gui.xaero_pac_claiming_as_player':'Zona personal',
 'gui.xaero_pac_claiming_as_party':'Zona del grupo',
 'gui.xaero_pac_claiming_as_server':'Zona del servidor',
 'gui.xaero_pac_ui_parties_and_claims':'Bases y grupos',
 'gui.xaero_pac_ui_main_menu':'Menú principal',
 'gui.xaero_pac_ui_config_menu':'Configurar permisos de tu base',
 'gui.xaero_pac_ui_about_party':'Ver grupo',
 'gui.xaero_pac_ui_claim':'Proteger','gui.xaero_pac_ui_unclaim':'Liberar',
 'gui.xaero_pac_ui_forceload':'Carga fija','gui.xaero_pac_ui_unforceload':'Sin carga',
 'gui.xaero_pac_ui_player_config':'Configuración personal',
 'gui.xaero_pac_ui_my_player_config':'Mis permisos',
 'gui.xaero_pac_ui_server_claims_config':'Zonas del servidor',
 'gui.xaero_pac_ui_expired_claims_config':'Zonas caducadas',
 'gui.xaero_pac_ui_wilderness_config':'Terreno libre',
 'gui.xaero_pac_ui_default_player_config':'Permisos predeterminados',
 'gui.xaero_pac_ui_party_claims_config':'Zonas del grupo',
 'gui.xaero_pac_ui_other_player_config_name_field':'Nombre del jugador',
 'gui.xaero_pac_ui_other_player_config_name_title':'Otro jugador:',
 'gui.xaero_pac_ui_other_player_config_button':'Editar permisos',
 'gui.xaero_pac_ui_other_player_config_waiting':'Esperando la configuración de %1$s…',
 'gui.xaero_pac_ui_other_player_config_waiting_cancel':'Cancelar',
 'gui.xaero_pac_ui_other_player_config':'Permisos de %1$s',
 'gui.xaero_pac_ui_player_config_refresh':'Actualizar',
 'gui.xaero_pac_ui_party_name':'Grupo: %1$s','gui.xaero_pac_ui_party_owner':'Dueño: %1$s',
 'gui.xaero_pac_ui_party_member_count':'Miembros: %1$s','gui.xaero_pac_ui_party_ally_count':'Aliados: %1$s',
 'gui.xaero_pac_ui_party_invite_count':'Invitaciones: %1$s',
 'gui.xaero_pac_ui_claim_count':'Zonas: %1$s','gui.xaero_pac_ui_claims_name':'Nombre: %1$s',
 'gui.xaero_pac_ui_forceload_count':'Carga fija: %1$s','gui.xaero_pac_ui_claims_color':'Color: %1$s',
 'gui.xaero_pac_ui_claiming_mode_dropdown_tooltip':'Titular de la zona',
 'gui.xaero_pac_title_wilderness':'Terreno libre',
 'gui.xaero_pac_title_server_claim':'Zona del servidor%1$s',
 'gui.xaero_pac_title_player_claim':'Zona de %1$s%2$s',
 'gui.xaero_claims_claim_already_claimed':'Esta zona ya está protegida.',
 'gui.xaero_claims_claim_already_claimed_by':'Esta zona pertenece a %1$s.',
 'gui.xaero_claims_claim_limit_reached':'Llegaste al límite de zonas protegidas.',
 'gui.xaero_claims_claim_unclaim_not_yours':'Sólo podés liberar tus propias zonas.',
 'gui.xaero_claims_claimed':'Zona protegida.','gui.xaero_claims_unclaimed':'Zona liberada.',
}
for key in ['other_player_config_syncing','player_config_syncing','party_syncing','claims_syncing']:
    claims['gui.xaero_pac_ui_'+key]='Sincronizando…'
for base in ['pack/client-overrides']+([] if args.staging_only else ['client/standard']):
    folder=ROOT/base/'resourcepacks'
    folder.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(folder/'Virgos-MC-UI.zip','w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('pack.mcmeta',json.dumps({'pack':{'pack_format':15,'description':'Virgos-MC · Códice, bases y grupos en español'}}))
        for lang in ['es_ar','es_es','es_mx','es_cl','es_uy','es_ve']:
            z.writestr(f'assets/heracles/lang/{lang}.json',json.dumps(labels,ensure_ascii=False))
            z.writestr(f'assets/openpartiesandclaims/lang/{lang}.json',json.dumps(claims,ensure_ascii=False))
    fancy=ROOT/base/'config/fancymenu/options.txt'
    if not fancy.exists():
        fancy.parent.mkdir(parents=True,exist_ok=True)
        fancy.write_text((ROOT/'client/standard/config/fancymenu/options.txt').read_text('utf-8'),'utf-8')
    text=fancy.read_text('utf-8').replace("B:show_customization_overlay = 'true';","B:show_customization_overlay = 'false';")
    text=text.replace("B:modpack_mode = 'false';","B:modpack_mode = 'true';")
    text=text.replace("S:custom_window_title = '';","S:custom_window_title = 'Virgos-MC | 1.20.1';")
    fancy.write_text(text,'utf-8')
    defaults=ROOT/base/'config/defaultoptions-common.toml'
    defaults.write_text('defaultDifficulty = "NORMAL"\nlockDifficulty = false\ndefaultResourcePacks = ["file/Virgos-MC-UI.zip"]\n','utf-8')
print('Spanish codex UI and clean menu defaults generated.')
