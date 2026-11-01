/**
 * hacs-refresh-card — the HACS check of HACS Refresh: status and progress, the last and next check, the updates
 * available for the repositories downloaded with HACS, and the ones that couldn't be checked.
 * Served and added to the dashboard resources by the integration.
 * https://github.com/juju35/ha-hacs-refresh
 */
var HACS_REFRESH_CARD_VERSION = '0.8.2';

const HR_I18N = {
  en: {
    title: 'HACS updates',
    up_to_date: 'Up to date',
    updates_one: '{n} update',
    updates_many: '{n} updates',
    checking: 'Checking {done}/{total}',
    checking_short: 'Checking…',
    error: 'Error',
    failed_one: '{n} failed',
    failed_many: '{n} failed',
    not_loaded: 'HACS Refresh is not set up',
    unavailable: 'Unavailable',
    never_checked: 'Not checked yet',
    checked: 'Checked {d}',
    next: 'next {d}',
    auto_off: 'automatic check off',
    check_now: 'Check for updates',
    updates_title: 'Updates available',
    no_updates: 'Every repository is up to date',
    no_details: 'HACS isn’t loaded: no details on these updates',
    failed_title: 'Could not be checked',
    error_title: 'The last check failed',
    install_all: 'Update all ({n})',
    installing: 'Installing… {n} left',
    installing_short: 'Installing…',
    confirm_one: 'Install {n} update?',
    confirm_many: 'Install {n} updates?',
    confirm_hint: 'One after the other. Integrations need a restart of Home Assistant afterwards.',
    cancel: 'Cancel',
    install: 'Install',
    install_failed_title: 'Could not be installed',
    version: '{from} → {to}',
    ed_entity: 'HACS Refresh sensor',
    ed_entity_helper: 'Status sensor; leave empty to find it automatically',
    ed_title: 'Title',
    ed_title_helper: 'Leave empty for “HACS updates”',
    ed_show_updates: 'Updates available',
    ed_show_updates_helper: 'The HACS repositories with an update, from their update entities',
    ed_show_failed: 'Repositories that could not be checked',
    ed_show_failed_helper: 'And the error of a check that failed',
    ed_check_button: '“Check for updates” button',
    ed_check_button_helper: 'Starts a check from the header',
    ed_install_button: '“Update all” button',
    ed_install_button_helper: 'Installs every update listed, after a confirmation (administrators only)',
    ed_hide_when_ok: 'Hide the card when everything is up to date',
    ed_hide_when_ok_helper: 'The card only appears while checking, or with an update or an error',
    ed_language: 'Language',
    ed_language_helper: 'Leave empty to follow Home Assistant',
  },
  fr: {
    title: 'Mises à jour HACS',
    up_to_date: 'À jour',
    updates_one: '{n} mise à jour',
    updates_many: '{n} mises à jour',
    checking: 'Vérification {done}/{total}',
    checking_short: 'Vérification…',
    error: 'Erreur',
    failed_one: '{n} en échec',
    failed_many: '{n} en échec',
    not_loaded: 'HACS Refresh n’est pas configuré',
    unavailable: 'Indisponible',
    never_checked: 'Pas encore vérifié',
    checked: 'Vérifié {d}',
    next: 'prochaine {d}',
    auto_off: 'vérification automatique désactivée',
    check_now: 'Rechercher les mises à jour',
    updates_title: 'Mises à jour disponibles',
    no_updates: 'Tous les dépôts sont à jour',
    no_details: 'HACS n’est pas chargé : pas de détail sur ces mises à jour',
    failed_title: 'Impossible à vérifier',
    error_title: 'La dernière vérification a échoué',
    install_all: 'Tout mettre à jour ({n})',
    installing: 'Installation… {n} restante(s)',
    installing_short: 'Installation…',
    confirm_one: 'Installer {n} mise à jour ?',
    confirm_many: 'Installer {n} mises à jour ?',
    confirm_hint: 'L’une après l’autre. Les intégrations demandent ensuite un redémarrage de Home Assistant.',
    cancel: 'Annuler',
    install: 'Installer',
    install_failed_title: 'Installation impossible',
    version: '{from} → {to}',
    ed_entity: 'Capteur HACS Refresh',
    ed_entity_helper: 'Capteur de statut ; laisser vide pour le trouver automatiquement',
    ed_title: 'Titre',
    ed_title_helper: 'Laisser vide pour « Mises à jour HACS »',
    ed_show_updates: 'Mises à jour disponibles',
    ed_show_updates_helper: 'Les dépôts HACS avec une mise à jour, d’après leurs entités de mise à jour',
    ed_show_failed: 'Dépôts impossibles à vérifier',
    ed_show_failed_helper: 'Et l’erreur d’une vérification qui a échoué',
    ed_check_button: 'Bouton « Rechercher les mises à jour »',
    ed_check_button_helper: 'Lance une vérification depuis l’en-tête',
    ed_install_button: 'Bouton « Tout mettre à jour »',
    ed_install_button_helper: 'Installe toutes les mises à jour listées, après confirmation (administrateurs uniquement)',
    ed_hide_when_ok: 'Masquer la carte quand tout est à jour',
    ed_hide_when_ok_helper: 'La carte n’apparaît que pendant une vérification, ou avec une mise à jour ou une erreur',
    ed_language: 'Langue',
    ed_language_helper: 'Laisser vide pour suivre Home Assistant',
  },
  de: {
    title: 'HACS-Updates',
    up_to_date: 'Aktuell',
    updates_one: '{n} Update',
    updates_many: '{n} Updates',
    checking: 'Prüfung {done}/{total}',
    checking_short: 'Prüfung läuft…',
    error: 'Fehler',
    failed_one: '{n} fehlgeschlagen',
    failed_many: '{n} fehlgeschlagen',
    not_loaded: 'HACS Refresh ist nicht eingerichtet',
    unavailable: 'Nicht verfügbar',
    never_checked: 'Noch nicht geprüft',
    checked: 'Geprüft {d}',
    next: 'nächste {d}',
    auto_off: 'automatische Prüfung aus',
    check_now: 'Nach Updates suchen',
    updates_title: 'Verfügbare Updates',
    no_updates: 'Alle Repositorys sind aktuell',
    no_details: 'HACS ist nicht geladen: keine Details zu diesen Updates',
    failed_title: 'Konnten nicht geprüft werden',
    error_title: 'Die letzte Prüfung ist fehlgeschlagen',
    install_all: 'Alle aktualisieren ({n})',
    installing: 'Installation… {n} übrig',
    installing_short: 'Installation…',
    confirm_one: '{n} Update installieren?',
    confirm_many: '{n} Updates installieren?',
    confirm_hint: 'Nacheinander. Integrationen erfordern danach einen Neustart von Home Assistant.',
    cancel: 'Abbrechen',
    install: 'Installieren',
    install_failed_title: 'Nicht installierbar',
    version: '{from} → {to}',
    ed_entity: 'HACS-Refresh-Sensor',
    ed_entity_helper: 'Statussensor; leer lassen, um ihn automatisch zu finden',
    ed_title: 'Titel',
    ed_title_helper: 'Leer lassen für „HACS-Updates“',
    ed_show_updates: 'Verfügbare Updates',
    ed_show_updates_helper: 'Die HACS-Repositorys mit einem Update, aus ihren Update-Entitäten',
    ed_show_failed: 'Nicht prüfbare Repositorys',
    ed_show_failed_helper: 'Und der Fehler einer fehlgeschlagenen Prüfung',
    ed_check_button: 'Schaltfläche „Nach Updates suchen“',
    ed_check_button_helper: 'Startet eine Prüfung aus der Kopfzeile',
    ed_install_button: 'Schaltfläche „Alle aktualisieren“',
    ed_install_button_helper: 'Installiert alle aufgeführten Updates nach einer Bestätigung (nur Administratoren)',
    ed_hide_when_ok: 'Karte ausblenden, wenn alles aktuell ist',
    ed_hide_when_ok_helper: 'Die Karte erscheint nur während einer Prüfung oder bei einem Update oder Fehler',
    ed_language: 'Sprache',
    ed_language_helper: 'Leer lassen, um Home Assistant zu folgen',
  },
  es: {
    title: 'Actualizaciones de HACS',
    up_to_date: 'Al día',
    updates_one: '{n} actualización',
    updates_many: '{n} actualizaciones',
    checking: 'Comprobando {done}/{total}',
    checking_short: 'Comprobando…',
    error: 'Error',
    failed_one: '{n} con error',
    failed_many: '{n} con error',
    not_loaded: 'HACS Refresh no está configurado',
    unavailable: 'No disponible',
    never_checked: 'Aún sin comprobar',
    checked: 'Comprobado {d}',
    next: 'próxima {d}',
    auto_off: 'comprobación automática desactivada',
    check_now: 'Buscar actualizaciones',
    updates_title: 'Actualizaciones disponibles',
    no_updates: 'Todos los repositorios están al día',
    no_details: 'HACS no está cargado: sin detalles de estas actualizaciones',
    failed_title: 'No se pudieron comprobar',
    error_title: 'La última comprobación falló',
    install_all: 'Actualizar todo ({n})',
    installing: 'Instalando… quedan {n}',
    installing_short: 'Instalando…',
    confirm_one: '¿Instalar {n} actualización?',
    confirm_many: '¿Instalar {n} actualizaciones?',
    confirm_hint: 'Una tras otra. Las integraciones requieren después reiniciar Home Assistant.',
    cancel: 'Cancelar',
    install: 'Instalar',
    install_failed_title: 'No se pudieron instalar',
    version: '{from} → {to}',
    ed_entity: 'Sensor de HACS Refresh',
    ed_entity_helper: 'Sensor de estado; déjalo vacío para encontrarlo automáticamente',
    ed_title: 'Título',
    ed_title_helper: 'Déjalo vacío para «Actualizaciones de HACS»',
    ed_show_updates: 'Actualizaciones disponibles',
    ed_show_updates_helper: 'Los repositorios de HACS con una actualización, según sus entidades de actualización',
    ed_show_failed: 'Repositorios que no se pudieron comprobar',
    ed_show_failed_helper: 'Y el error de una comprobación fallida',
    ed_check_button: 'Botón «Buscar actualizaciones»',
    ed_check_button_helper: 'Lanza una comprobación desde la cabecera',
    ed_install_button: 'Botón «Actualizar todo»',
    ed_install_button_helper: 'Instala todas las actualizaciones listadas, tras una confirmación (solo administradores)',
    ed_hide_when_ok: 'Ocultar la tarjeta cuando todo esté al día',
    ed_hide_when_ok_helper: 'La tarjeta solo aparece durante una comprobación, o con una actualización o un error',
    ed_language: 'Idioma',
    ed_language_helper: 'Déjalo vacío para seguir a Home Assistant',
  },
  sr: {
    title: 'HACS ажурирања',
    up_to_date: 'Ажурирано',
    updates_one: '{n} ажурирање',
    updates_many: '{n} ажурирања',
    checking: 'Провера {done}/{total}',
    checking_short: 'Проверавање…',
    error: 'Грешка',
    failed_one: '{n} неуспешан',
    failed_many: '{n} неуспешних',
    not_loaded: 'HACS Refresh није подешен',
    unavailable: 'Недоступно',
    never_checked: 'Још није проверено',
    checked: 'Проверено {d}',
    next: 'следећа {d}',
    auto_off: 'аутоматска провера искључена',
    check_now: 'Провери ажурирања',
    updates_title: 'Доступна ажурирања',
    no_updates: 'Сви репозиторијуми су ажурирани',
    no_details: 'HACS није учитан: нема детаља о овим ажурирањима',
    failed_title: 'Није могуће проверити',
    error_title: 'Последња провера није успела',
    install_all: 'Ажурирај све ({n})',
    installing: 'Инсталирање… преостало {n}',
    installing_short: 'Инсталирање…',
    confirm_one: 'Инсталирати {n} ажурирање?',
    confirm_many: 'Инсталирати {n} ажурирања?',
    confirm_hint: 'Једно за другим. Интеграције након тога захтевају поновно покретање Home Assistant-а.',
    cancel: 'Откажи',
    install: 'Инсталирај',
    install_failed_title: 'Није могуће инсталирати',
    version: '{from} → {to}',
    ed_entity: 'HACS Refresh сензор',
    ed_entity_helper: 'Сензор статуса; оставите празно да би се аутоматски пронашао',
    ed_title: 'Наслов',
    ed_title_helper: 'Оставите празно за „HACS ажурирања“',
    ed_show_updates: 'Доступна ажурирања',
    ed_show_updates_helper: 'HACS репозиторијуми са ажурирањем, према њиховим ентитетима ажурирања',
    ed_show_failed: 'Репозиторијуми које није могуће проверити',
    ed_show_failed_helper: 'И грешка провере која није успела',
    ed_check_button: 'Дугме „Провери ажурирања“',
    ed_check_button_helper: 'Покреће проверу из заглавља',
    ed_install_button: 'Дугме „Ажурирај све“',
    ed_install_button_helper: 'Инсталира сва наведена ажурирања, након потврде (само администратори)',
    ed_hide_when_ok: 'Сакриј картицу када је све ажурирано',
    ed_hide_when_ok_helper: 'Картица се појављује само током провере, или када постоји ажурирање или грешка',
    ed_language: 'Језик',
    ed_language_helper: 'Оставите празно да бисте пратили Home Assistant',
  },
  'sr-Latn': {
    title: 'HACS ažuriranja',
    up_to_date: 'Ažurirano',
    updates_one: '{n} ažuriranje',
    updates_many: '{n} ažuriranja',
    checking: 'Provera {done}/{total}',
    checking_short: 'Proveravanje…',
    error: 'Greška',
    failed_one: '{n} neuspešan',
    failed_many: '{n} neuspešnih',
    not_loaded: 'HACS Refresh nije podešen',
    unavailable: 'Nedostupno',
    never_checked: 'Još nije provereno',
    checked: 'Provereno {d}',
    next: 'sledeća {d}',
    auto_off: 'automatska provera isključena',
    check_now: 'Proveri ažuriranja',
    updates_title: 'Dostupna ažuriranja',
    no_updates: 'Svi repozitorijumi su ažurirani',
    no_details: 'HACS nije učitan: nema detalja o ovim ažuriranjima',
    failed_title: 'Nije moguće proveriti',
    error_title: 'Poslednja provera nije uspela',
    install_all: 'Ažuriraj sve ({n})',
    installing: 'Instaliranje… preostalo {n}',
    installing_short: 'Instaliranje…',
    confirm_one: 'Instalirati {n} ažuriranje?',
    confirm_many: 'Instalirati {n} ažuriranja?',
    confirm_hint: 'Jedno za drugim. Integracije nakon toga zahtevaju ponovno pokretanje Home Assistant-a.',
    cancel: 'Otkaži',
    install: 'Instaliraj',
    install_failed_title: 'Nije moguće instalirati',
    version: '{from} → {to}',
    ed_entity: 'HACS Refresh senzor',
    ed_entity_helper: 'Senzor statusa; ostavite prazno da bi se automatski pronašao',
    ed_title: 'Naslov',
    ed_title_helper: 'Ostavite prazno za „HACS ažuriranja“',
    ed_show_updates: 'Dostupna ažuriranja',
    ed_show_updates_helper: 'HACS repozitorijumi sa ažuriranjem, prema njihovim entitetima ažuriranja',
    ed_show_failed: 'Repozitorijumi koje nije moguće proveriti',
    ed_show_failed_helper: 'I greška provere koja nije uspela',
    ed_check_button: 'Dugme „Proveri ažuriranja“',
    ed_check_button_helper: 'Pokreće proveru iz zaglavlja',
    ed_install_button: 'Dugme „Ažuriraj sve“',
    ed_install_button_helper: 'Instalira sva navedena ažuriranja, nakon potvrde (samo administratori)',
    ed_hide_when_ok: 'Sakrij karticu kada je sve ažurirano',
    ed_hide_when_ok_helper: 'Kartica se pojavljuje samo tokom provere, ili kada postoji ažuriranje ili greška',
    ed_language: 'Jezik',
    ed_language_helper: 'Ostavite prazno da biste pratili Home Assistant',
  },
  it: {
    title: 'Aggiornamenti HACS',
    up_to_date: 'Aggiornato',
    updates_one: '{n} aggiornamento',
    updates_many: '{n} aggiornamenti',
    checking: 'Verifica {done}/{total}',
    checking_short: 'Verifica in corso…',
    error: 'Errore',
    failed_one: '{n} fallito',
    failed_many: '{n} falliti',
    not_loaded: 'HACS Refresh non è configurato',
    unavailable: 'Non disponibile',
    never_checked: 'Non ancora verificato',
    checked: 'Verificato {d}',
    next: 'prossima {d}',
    auto_off: 'verifica automatica disattivata',
    check_now: 'Cerca aggiornamenti',
    updates_title: 'Aggiornamenti disponibili',
    no_updates: 'Tutti i repository sono aggiornati',
    no_details: 'HACS non è caricato: nessun dettaglio su questi aggiornamenti',
    failed_title: 'Impossibile verificare',
    error_title: 'L’ultima verifica non è riuscita',
    install_all: 'Aggiorna tutto ({n})',
    installing: 'Installazione… {n} rimanenti',
    installing_short: 'Installazione…',
    confirm_one: 'Installare {n} aggiornamento?',
    confirm_many: 'Installare {n} aggiornamenti?',
    confirm_hint: 'Uno dopo l’altro. Le integrazioni richiedono poi un riavvio di Home Assistant.',
    cancel: 'Annulla',
    install: 'Installa',
    install_failed_title: 'Impossibile installare',
    version: '{from} → {to}',
    ed_entity: 'Sensore HACS Refresh',
    ed_entity_helper: 'Sensore di stato; lascia vuoto per trovarlo automaticamente',
    ed_title: 'Titolo',
    ed_title_helper: 'Lascia vuoto per «Aggiornamenti HACS»',
    ed_show_updates: 'Aggiornamenti disponibili',
    ed_show_updates_helper: 'I repository HACS con un aggiornamento, dalle loro entità di aggiornamento',
    ed_show_failed: 'Repository che non è stato possibile verificare',
    ed_show_failed_helper: 'E l’errore di una verifica non riuscita',
    ed_check_button: 'Pulsante «Cerca aggiornamenti»',
    ed_check_button_helper: 'Avvia una verifica dall’intestazione',
    ed_install_button: 'Pulsante «Aggiorna tutto»',
    ed_install_button_helper: 'Installa tutti gli aggiornamenti elencati, dopo una conferma (solo amministratori)',
    ed_hide_when_ok: 'Nascondi la scheda quando è tutto aggiornato',
    ed_hide_when_ok_helper: 'La scheda appare solo durante una verifica, o con un aggiornamento o un errore',
    ed_language: 'Lingua',
    ed_language_helper: 'Lascia vuoto per seguire Home Assistant',
  },
  nl: {
    title: 'HACS-updates',
    up_to_date: 'Up-to-date',
    updates_one: '{n} update',
    updates_many: '{n} updates',
    checking: 'Controleren {done}/{total}',
    checking_short: 'Controleren…',
    error: 'Fout',
    failed_one: '{n} mislukt',
    failed_many: '{n} mislukt',
    not_loaded: 'HACS Refresh is niet ingesteld',
    unavailable: 'Niet beschikbaar',
    never_checked: 'Nog niet gecontroleerd',
    checked: 'Gecontroleerd {d}',
    next: 'volgende {d}',
    auto_off: 'automatische controle uit',
    check_now: 'Controleren op updates',
    updates_title: 'Beschikbare updates',
    no_updates: 'Alle repository’s zijn up-to-date',
    no_details: 'HACS is niet geladen: geen details over deze updates',
    failed_title: 'Kon niet worden gecontroleerd',
    error_title: 'De laatste controle is mislukt',
    install_all: 'Alles bijwerken ({n})',
    installing: 'Installeren… nog {n}',
    installing_short: 'Installeren…',
    confirm_one: '{n} update installeren?',
    confirm_many: '{n} updates installeren?',
    confirm_hint: 'De een na de ander. Integraties vereisen daarna een herstart van Home Assistant.',
    cancel: 'Annuleren',
    install: 'Installeren',
    install_failed_title: 'Kon niet worden geïnstalleerd',
    version: '{from} → {to}',
    ed_entity: 'HACS Refresh-sensor',
    ed_entity_helper: 'Statussensor; laat leeg om hem automatisch te vinden',
    ed_title: 'Titel',
    ed_title_helper: 'Laat leeg voor “HACS-updates”',
    ed_show_updates: 'Beschikbare updates',
    ed_show_updates_helper: 'De HACS-repository’s met een update, volgens hun update-entiteiten',
    ed_show_failed: 'Repository’s die niet konden worden gecontroleerd',
    ed_show_failed_helper: 'En de fout van een mislukte controle',
    ed_check_button: 'Knop “Controleren op updates”',
    ed_check_button_helper: 'Start een controle vanuit de koptekst',
    ed_install_button: 'Knop “Alles bijwerken”',
    ed_install_button_helper: 'Installeert alle vermelde updates, na een bevestiging (alleen beheerders)',
    ed_hide_when_ok: 'Kaart verbergen als alles up-to-date is',
    ed_hide_when_ok_helper: 'De kaart verschijnt alleen tijdens een controle, of bij een update of een fout',
    ed_language: 'Taal',
    ed_language_helper: 'Laat leeg om Home Assistant te volgen',
  },
  pt: {
    title: 'Atualizações HACS',
    up_to_date: 'Atualizado',
    updates_one: '{n} atualização',
    updates_many: '{n} atualizações',
    checking: 'A verificar {done}/{total}',
    checking_short: 'A verificar…',
    error: 'Erro',
    failed_one: '{n} falhou',
    failed_many: '{n} falharam',
    not_loaded: 'HACS Refresh não configurado',
    unavailable: 'Indisponível',
    never_checked: 'Ainda não verificado',
    checked: 'Verificado {d}',
    next: 'próxima {d}',
    auto_off: 'verificação automática desativada',
    check_now: 'Procurar atualizações',
    updates_title: 'Atualizações disponíveis',
    no_updates: 'Todos os repositórios estão atualizados',
    no_details: 'O HACS não está carregado: sem detalhes sobre estas atualizações',
    failed_title: 'Não foi possível verificar',
    error_title: 'A última verificação falhou',
    install_all: 'Atualizar tudo ({n})',
    installing: 'A instalar… faltam {n}',
    installing_short: 'A instalar…',
    confirm_one: 'Instalar {n} atualização?',
    confirm_many: 'Instalar {n} atualizações?',
    confirm_hint: 'Uma após a outra. As integrações precisam depois de um reinício do Home Assistant.',
    cancel: 'Cancelar',
    install: 'Instalar',
    install_failed_title: 'Não foi possível instalar',
    version: '{from} → {to}',
    ed_entity: 'Sensor HACS Refresh',
    ed_entity_helper: 'Sensor de estado; deixe vazio para o encontrar automaticamente',
    ed_title: 'Título',
    ed_title_helper: 'Deixe vazio para «Atualizações HACS»',
    ed_show_updates: 'Atualizações disponíveis',
    ed_show_updates_helper: 'Os repositórios HACS com uma atualização, segundo as suas entidades de atualização',
    ed_show_failed: 'Repositórios que não foi possível verificar',
    ed_show_failed_helper: 'E o erro de uma verificação que falhou',
    ed_check_button: 'Botão «Procurar atualizações»',
    ed_check_button_helper: 'Inicia uma verificação a partir do cabeçalho',
    ed_install_button: 'Botão «Atualizar tudo»',
    ed_install_button_helper: 'Instala todas as atualizações listadas, após confirmação (apenas administradores)',
    ed_hide_when_ok: 'Ocultar o cartão quando tudo estiver atualizado',
    ed_hide_when_ok_helper: 'O cartão só aparece durante uma verificação, ou com uma atualização ou um erro',
    ed_language: 'Idioma',
    ed_language_helper: 'Deixe vazio para seguir o Home Assistant',
  },
  pl: {
    title: 'Aktualizacje HACS',
    up_to_date: 'Aktualne',
    updates_one: '{n} aktualizacja',
    updates_many: 'Aktualizacje: {n}',
    checking: 'Sprawdzanie {done}/{total}',
    checking_short: 'Sprawdzanie…',
    error: 'Błąd',
    failed_one: 'Nieudane: {n}',
    failed_many: 'Nieudane: {n}',
    not_loaded: 'HACS Refresh nieskonfigurowany',
    unavailable: 'Niedostępne',
    never_checked: 'Jeszcze nie sprawdzono',
    checked: 'Sprawdzono {d}',
    next: 'następne {d}',
    auto_off: 'automatyczne sprawdzanie wyłączone',
    check_now: 'Sprawdź aktualizacje',
    updates_title: 'Dostępne aktualizacje',
    no_updates: 'Wszystkie repozytoria są aktualne',
    no_details: 'HACS nie jest załadowany: brak szczegółów tych aktualizacji',
    failed_title: 'Nie udało się sprawdzić',
    error_title: 'Ostatnie sprawdzanie nie powiodło się',
    install_all: 'Zaktualizuj wszystko ({n})',
    installing: 'Instalowanie… pozostało: {n}',
    installing_short: 'Instalowanie…',
    confirm_one: 'Zainstalować {n} aktualizację?',
    confirm_many: 'Zainstalować aktualizacje ({n})?',
    confirm_hint: 'Jedna po drugiej. Integracje wymagają potem ponownego uruchomienia Home Assistant.',
    cancel: 'Anuluj',
    install: 'Zainstaluj',
    install_failed_title: 'Nie udało się zainstalować',
    version: '{from} → {to}',
    ed_entity: 'Czujnik HACS Refresh',
    ed_entity_helper: 'Czujnik stanu; pozostaw puste, aby znaleźć go automatycznie',
    ed_title: 'Tytuł',
    ed_title_helper: 'Pozostaw puste dla „Aktualizacje HACS”',
    ed_show_updates: 'Dostępne aktualizacje',
    ed_show_updates_helper: 'Repozytoria HACS z aktualizacją, według ich encji aktualizacji',
    ed_show_failed: 'Repozytoria, których nie udało się sprawdzić',
    ed_show_failed_helper: 'Oraz błąd nieudanego sprawdzania',
    ed_check_button: 'Przycisk „Sprawdź aktualizacje”',
    ed_check_button_helper: 'Uruchamia sprawdzanie z nagłówka',
    ed_install_button: 'Przycisk „Zaktualizuj wszystko”',
    ed_install_button_helper: 'Instaluje wszystkie wymienione aktualizacje po potwierdzeniu (tylko administratorzy)',
    ed_hide_when_ok: 'Ukryj kartę, gdy wszystko jest aktualne',
    ed_hide_when_ok_helper: 'Karta pojawia się tylko podczas sprawdzania albo gdy jest aktualizacja lub błąd',
    ed_language: 'Język',
    ed_language_helper: 'Pozostaw puste, aby używać języka Home Assistant',
  },
};

// The full code when the card has it (sr-Latn), else the part before the dash (fr-FR → fr, pt-BR → pt), else English.
const hrLang = (hass, config) => {
  const raw = String(config?.language || hass?.locale?.language || hass?.language || 'en');
  if (HR_I18N[raw]) return raw;
  const l = raw.split('-')[0];
  return HR_I18N[l] ? l : 'en';
};

// Locale for Intl: Home Assistant's full locale (pt-BR, fr-CA…) when its base is the card's language, else the card's
// language (option `language:` set to another one, or a code the card has its own strings for: sr vs sr-Latn).
// A bare `pt` is Home Assistant's European Portuguese: Intl reads it as Brazilian, so it becomes pt-PT.
const hrLocale = (hass, config) => {
  const lang = hrLang(hass, config);
  const full = String(hass?.locale?.language || hass?.language || '');
  const loc = full === lang || (!HR_I18N[full] && full.split('-')[0] === lang) ? full || lang : lang;
  return loc === 'pt' ? 'pt-PT' : loc;
};

const hrT = (lang, key, vars = {}) =>
  (HR_I18N[lang]?.[key] ?? HR_I18N.en[key] ?? key).replace(/\{(\w+)\}/g, (_, k) => vars[k] ?? '');

const hrEsc = (s) =>
  String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);

const HR_DEFAULTS = { show_updates: true, show_failed: true, check_button: true, install_button: true, hide_when_ok: false };

// The integration's entities, from the entity registry: { device: { status, last_check, button } }.
// Each entity is told apart by its translation key, else by the end of its entity ID (renamed IDs keep the key).
const HR_KEYS = { status: '_status', last_check: '_last_check', check_updates: '_check_for_updates' };
function hrDevices(registry) {
  const devices = {};
  for (const [id, e] of Object.entries(registry || {})) {
    if (e?.platform !== 'hacs_refresh') continue;
    const d = (devices[e.device_id || ''] ||= {});
    const key = Object.keys(HR_KEYS).find((k) => e.translation_key === k) || Object.keys(HR_KEYS).find((k) => id.endsWith(HR_KEYS[k]));
    if (!key) continue;
    d[key === 'check_updates' ? 'button' : key] = id;
  }
  return devices;
}

// HACS' own update entities: one per downloaded repository.
const hrHacsUpdates = (registry) =>
  Object.keys(registry || {}).filter((id) => id.startsWith('update.') && registry[id]?.platform === 'hacs');

class HacsRefreshCard extends HTMLElement {
  static getConfigElement() {
    return document.createElement('hacs-refresh-card-editor');
  }

  static getStubConfig() {
    return {};
  }

  setConfig(config) {
    this._config = { ...HR_DEFAULTS, ...config };
    if (!this.shadowRoot) this.attachShadow({ mode: 'open' });
    this._sig = null;
    this._render();
  }

  set hass(hass) {
    const old = this._hass;
    this._hass = hass;
    // Nothing the card shows changed: the same state objects, registry, language and minute ("3 min ago").
    const watched = this._watched;
    if (
      old &&
      this._sig &&
      watched &&
      hass.entities === old.entities &&
      watched.every((id) => hass.states[id] === old.states[id]) &&
      hrLocale(hass, this._config) === hrLocale(old, this._config) &&
      Math.floor(Date.now() / 60000) === this._sigMinute
    ) {
      return;
    }
    this._render();
  }

  getCardSize() {
    return 2 + (this._rows || 0);
  }

  getGridOptions() {
    return { columns: 12, min_columns: 6, rows: 'auto' };
  }

  _t(key, vars) {
    return hrT(hrLang(this._hass, this._config), key, vars);
  }

  // "3 hours ago", "in 21 hours"… in the card's language.
  _relative(iso) {
    const t = new Date(iso).getTime();
    if (!Number.isFinite(t)) return '';
    const m = (t - Date.now()) / 60000;
    let rtf;
    try {
      rtf = new Intl.RelativeTimeFormat(hrLocale(this._hass, this._config), { numeric: 'auto' });
    } catch {
      return new Date(t).toISOString();
    }
    // Rounded to the nearest unit: a check due in 20 h 59 min reads "in 21 hours".
    const a = Math.abs(m);
    if (a < 1) return rtf.format(0, 'second');
    if (a < 59.5) return rtf.format(Math.round(m), 'minute');
    if (a < 2850) return rtf.format(Math.round(m / 60), 'hour');
    return rtf.format(Math.round(m / 1440), 'day');
  }

  _absolute(iso) {
    const d = new Date(iso);
    if (!Number.isFinite(d.getTime())) return '';
    try {
      return d.toLocaleString(hrLocale(this._hass, this._config), { dateStyle: 'medium', timeStyle: 'short' });
    } catch {
      return d.toISOString();
    }
  }

  // The integration's entities (cached per registry object, never when empty) and HACS' update entities.
  _lookup() {
    const registry = this._hass.entities;
    if (!this._reg || this._reg.registry !== registry) {
      const devices = hrDevices(registry);
      this._reg = Object.keys(devices).length ? { registry, devices, updates: hrHacsUpdates(registry) } : null;
    }
    const devices = this._reg?.devices || {};
    const updates = this._reg?.updates || [];
    let status = this._config.entity;
    if (!status) status = Object.values(devices).map((d) => d.status).find((id) => this._hass.states[id]);
    if (!status) return { updates };
    // Any of the device's entities (the Last check sensor, the button) leads to its status sensor.
    const device = Object.values(devices).find((d) => Object.values(d).includes(status));
    return device?.status ? { ...device, updates } : { ...device, status, updates };
  }

  _render() {
    if (!this._config || !this._hass || !this.shadowRoot) return;
    const c = this._config;
    const ids = this._lookup();
    const states = this._hass.states;
    const raw = ids.status && states[ids.status];
    // Unavailable or unknown (entry not loaded, setup retry, restored state): nothing to read from it.
    const unavailable = !!raw && ['unavailable', 'unknown'].includes(raw.state);
    const st = unavailable ? null : raw;
    const lastSt = ids.last_check && states[ids.last_check];
    const buttonSt = ids.button && states[ids.button];
    this._watched = [ids.status, ids.last_check, ids.button, ...ids.updates].filter(Boolean);
    this._ids = ids;

    const minute = Math.floor(Date.now() / 60000);
    this._sigMinute = minute;
    const updateStates = ids.updates.map((id) => states[id]).filter((s) => s?.state === 'on');
    // Every update entity's state, not only the ones on: one coming back from unavailable changes the count.
    const updateSig = ids.updates.map((id) => states[id]?.state);
    const admin = !!this._hass.user?.is_admin;
    const sig = JSON.stringify([c, hrLocale(this._hass, c), ids, raw, lastSt, buttonSt?.state, updateStates, updateSig, minute, admin, !!this._confirm]);
    if (sig === this._sig) return;
    this._sig = sig;

    const a = st?.attributes || {};
    const running = st?.state === 'running';
    const failed = Array.isArray(a.failed) ? a.failed : [];
    const installing = Array.isArray(a.installing) ? a.installing : [];
    const installFailed = Array.isArray(a.install_failed) ? a.install_failed : [];
    const error = st?.state === 'error' ? a.error || this._t('error') : null;
    // The update entities are the truth; the sensor's count is the fallback when HACS' entities aren't there.
    const updates = updateStates
      .map((s) => ({
        id: s.entity_id,
        title: s.attributes.title || s.attributes.friendly_name || s.entity_id,
        from: s.attributes.installed_version,
        to: s.attributes.latest_version,
        picture: s.attributes.entity_picture,
      }))
      .sort((x, y) => String(x.title).localeCompare(String(y.title)));
    // HACS not loaded (setup retry, disabled): its entities are unavailable or gone, so they say nothing.
    const known = ids.updates.some((id) => ['on', 'off'].includes(states[id]?.state));
    const count = known ? updates.length : Number(a.updates) || 0;
    const level = !st ? 'na' : error ? 'alert' : failed.length || installFailed.length ? 'warn' : running || installing.length || count ? 'info' : 'ok';

    const hidden = c.hide_when_ok && st && level === 'ok';
    this.style.display = hidden ? 'none' : '';
    if (hidden) return;

    const shownUpdates = c.show_updates && st ? updates : [];
    this._rows = shownUpdates.length + (c.show_failed ? failed.length + installFailed.length : 0);
    // Installed from the card: what it lists (and the confirmation counts) is what gets installed.
    this._installable = st && admin && c.install_button && !installing.length ? updates.map((u) => u.id) : [];
    if (!this._installable.length) this._confirm = false;

    const last = lastSt && !['unknown', 'unavailable'].includes(lastSt.state) ? lastSt.state : null;
    // A check already due (overdue, or retried within the hour while HACS is unavailable) has no "next" to show.
    const nextAt = lastSt?.attributes?.next_check;
    const next = nextAt && new Date(nextAt).getTime() > Date.now() ? nextAt : null;
    const interval = lastSt?.attributes?.scan_interval;
    const subtitle = !st
      ? ''
      : [
          last ? this._t('checked', { d: this._relative(last) }) : this._t('never_checked'),
          interval === 0 ? this._t('auto_off') : next ? this._t('next', { d: this._relative(next) }) : '',
        ]
          .filter(Boolean)
          .join(' · ');
    const icon = { ok: 'mdi:package-variant-closed-check', info: 'mdi:package-up', warn: 'mdi:package-variant-closed-remove', alert: 'mdi:alert-circle-outline', na: 'mdi:package-variant-closed' }[level];
    const pct = running && a.total ? Math.round((100 * (a.done || 0)) / a.total) : 0;

    // innerHTML replaces the focused element: give the focus back to its new copy afterwards.
    const active = this.shadowRoot.activeElement;
    const focusCls = ['check', 'install', 'confirm-yes', 'confirm-no'].find((k) => active?.classList?.contains(k));
    const focus = focusCls || (active?.dataset?.id ? { id: active.dataset.id } : null);
    // The button is also unavailable while updates are installed: grey it out right away, without waiting for its state.
    this._busy = running || installing.length > 0 || buttonSt?.state === 'unavailable';
    this.shadowRoot.innerHTML = `
      <style>${HacsRefreshCard.styles}</style>
      <ha-card class="lvl-${level}">
        <div class="head">
          <div class="badge"><ha-icon icon="${icon}"></ha-icon></div>
          <div class="heading">
            <div class="title">${hrEsc(c.title || this._t('title'))}</div>
            ${subtitle ? `<div class="subtitle" title="${hrEsc(last ? this._absolute(last) : '')}">${hrEsc(subtitle)}</div>` : ''}
          </div>
          ${this._checkButton(this._busy)}
          <div class="pill">${hrEsc(unavailable ? this._t('unavailable') : this._status(st, running, a, count, failed, error, installing))}</div>
        </div>
        ${this._confirm ? this._confirmBox(this._installable.length) : ''}
        ${running ? `<div class="progress" role="progressbar" aria-valuenow="${pct}" aria-valuemin="0" aria-valuemax="100"><span style="width:${pct}%"></span></div>` : ''}
        ${c.show_failed && error ? `<div class="error"><ha-icon icon="mdi:alert-circle-outline"></ha-icon><span><b>${hrEsc(this._t('error_title'))}</b><br>${hrEsc(error)}</span></div>` : ''}
        ${
          c.show_updates && st
            ? this._section(
                'updates_title',
                shownUpdates.length
                  ? shownUpdates.map((u) => this._updateRow(u, installing.includes(u.id))).join('')
                  : `<div class="empty">${hrEsc(this._t(count ? 'no_details' : 'no_updates'))}</div>`,
                count,
                this._installButton(installing),
              )
            : ''
        }
        ${c.show_failed && failed.length ? this._section('failed_title', failed.map((f) => this._failedRow(f)).join('')) : ''}
        ${c.show_failed && installFailed.length ? this._section('install_failed_title', installFailed.map((f) => this._failedRow(f)).join('')) : ''}
      </ha-card>`;

    const check = this.shadowRoot.querySelector('.check');
    check?.addEventListener('click', () => this._check());
    if (focus === 'check') check?.focus();
    const on = (cls, fn) => {
      const el = this.shadowRoot.querySelector(`.${cls}`);
      el?.addEventListener('click', fn);
      if (focus === cls) el?.focus();
    };
    on('install', () => this._askInstall());
    on('confirm-yes', () => this._install());
    on('confirm-no', () => this._setConfirm(false));
    for (const el of this.shadowRoot.querySelectorAll('.row[data-id]')) {
      el.addEventListener('click', () => this._moreInfo(el.dataset.id));
      if (focus?.id === el.dataset.id) el.focus();
    }
    // A repository picture that doesn't load falls back to the generic icon.
    for (const img of this.shadowRoot.querySelectorAll('img.pic')) {
      img.addEventListener('error', () => img.parentElement?.classList.add('nopic'), { once: true });
    }
  }

  _status(st, running, a, count, failed, error, installing = []) {
    if (!st) return this._t('not_loaded');
    if (running) return a.total ? this._t('checking', { done: a.done || 0, total: a.total }) : this._t('checking_short');
    if (installing.length) return this._t('installing', { n: installing.length });
    if (error) return this._t('error');
    const parts = [];
    if (count) parts.push(this._t(count > 1 ? 'updates_many' : 'updates_one', { n: count }));
    if (failed.length) parts.push(this._t(failed.length > 1 ? 'failed_many' : 'failed_one', { n: failed.length }));
    return parts.length ? parts.join(' · ') : this._t('up_to_date');
  }

  _checkButton(busy) {
    if (!this._config.check_button || !this._ids.button) return '';
    const label = hrEsc(this._t('check_now'));
    // aria-disabled rather than disabled: a disabled button would drop the keyboard focus while checking.
    return `<button class="check" title="${label}" aria-label="${label}"${busy ? ' aria-disabled="true"' : ''}><ha-icon icon="mdi:refresh"></ha-icon></button>`;
  }

  _check() {
    if (this._ids.button && !this._busy) this._hass.callService('button', 'press', { entity_id: this._ids.button });
  }

  // The updates section's button: "Update all (n)", or the installs' progress while they run.
  _installButton(installing) {
    if (installing.length) {
      return `<span class="install busy" aria-live="polite"><ha-icon icon="mdi:progress-download"></ha-icon>${hrEsc(this._t('installing_short'))}</span>`;
    }
    const n = this._installable.length;
    if (!n) return '';
    const label = hrEsc(this._t('install_all', { n }));
    return `<button class="install"${this._confirm ? ' aria-expanded="true"' : ''}><ha-icon icon="mdi:package-down"></ha-icon>${label}</button>`;
  }

  // Confirmation at the top of the card, like the other cards' popups.
  _confirmBox(n) {
    return `
        <div class="confirm" role="alertdialog" aria-label="${hrEsc(this._t(n > 1 ? 'confirm_many' : 'confirm_one', { n }))}">
          <ha-icon icon="mdi:package-down"></ha-icon>
          <span class="ctext"><b>${hrEsc(this._t(n > 1 ? 'confirm_many' : 'confirm_one', { n }))}</b><br>${hrEsc(this._t('confirm_hint'))}</span>
          <span class="cbtns">
            <button class="confirm-no">${hrEsc(this._t('cancel'))}</button>
            <button class="confirm-yes">${hrEsc(this._t('install'))}</button>
          </span>
        </div>`;
  }

  _setConfirm(on) {
    this._confirm = on;
    this._sig = null;
    this._render();
    // Keyboard focus on the safe choice when it opens, back on the button when it closes.
    this.shadowRoot?.querySelector(on ? '.confirm-no' : '.install')?.focus?.();
  }

  _askInstall() {
    if (this._installable.length) this._setConfirm(true);
  }

  _install() {
    const ids = this._installable;
    this._setConfirm(false);
    if (!ids.length) return;
    // Home Assistant shows the error of a failed call; nothing more to do with it here.
    Promise.resolve(this._hass.callService('hacs_refresh', 'install_updates', { entity_id: ids })).catch(() => {});
  }

  _moreInfo(entityId) {
    const ev = new Event('hass-more-info', { bubbles: true, composed: true });
    ev.detail = { entityId };
    this.dispatchEvent(ev);
  }

  // A section, with its number of items in the title ("Updates available · 3") and an action on its right.
  _section(key, body, count = 0, action = '') {
    const n = count ? ` <span class="count">· ${count}</span>` : '';
    return `<div class="section"><div class="shead"><div class="stitle">${hrEsc(this._t(key))}${n}</div>${action}</div><div class="list">${body}</div></div>`;
  }

  _updateRow(u, busy = false) {
    const version = u.from && u.to ? this._t('version', { from: u.from, to: u.to }) : u.to || '';
    const pic = u.picture && !busy ? `<img class="pic" src="${hrEsc(u.picture)}" alt="" loading="lazy" referrerpolicy="no-referrer">` : '';
    return `
          <button class="row upd${busy ? ' busy' : ''}" data-id="${hrEsc(u.id)}" title="${hrEsc(u.title)}">
            <span class="ic${pic ? '' : ' nopic'}">${pic}<ha-icon icon="${busy ? 'mdi:progress-download' : 'mdi:package-up'}"></ha-icon></span>
            <span class="txt">
              <span class="name">${hrEsc(u.title)}</span>
              ${version ? `<span class="sub">${hrEsc(version)}</span>` : ''}
            </span>
            <ha-icon class="chev" icon="mdi:chevron-right"></ha-icon>
          </button>`;
  }

  // "owner/repo" or "owner/repo: the error".
  _failedRow(f) {
    const text = String(f);
    const i = text.indexOf(': ');
    const name = i > 0 ? text.slice(0, i) : text;
    const why = i > 0 ? text.slice(i + 2) : '';
    return `
          <div class="row warn" title="${hrEsc(text)}">
            <span class="ic nopic"><ha-icon icon="mdi:alert-outline"></ha-icon></span>
            <span class="txt">
              <span class="name">${hrEsc(name)}</span>
              ${why ? `<span class="sub">${hrEsc(why)}</span>` : ''}
            </span>
          </div>`;
  }

  static get styles() {
    return `
      :host {
        --hr-ok: var(--success-color, #43a047);
        --hr-info: var(--info-color, #039be5);
        --hr-warn: var(--warning-color, #ffa600);
        --hr-alert: var(--error-color, #db4437);
        --hr-na: var(--disabled-color, #9e9e9e);
      }
      /* Text and status icons in a state colour are mixed with the text colour: darker on a light theme,
         lighter on a dark one, so they stay readable (4.5:1 for text, 3:1 for icons) on their tinted background. */
      ha-card { padding: 12px; overflow: hidden; }
      ha-card.lvl-ok    { --c: var(--hr-ok); }
      ha-card.lvl-info  { --c: var(--hr-info); }
      ha-card.lvl-warn  { --c: var(--hr-warn); }
      ha-card.lvl-alert { --c: var(--hr-alert); }
      ha-card.lvl-na    { --c: var(--hr-na); }

      .head { display: flex; align-items: center; gap: 10px; }
      .badge { flex: none; width: 40px; height: 40px; border-radius: 50%; display: grid; place-items: center;
               background: color-mix(in srgb, var(--c) 16%, transparent); color: color-mix(in srgb, var(--c) 55%, var(--primary-text-color, #212121)); }
      .badge ha-icon { --mdc-icon-size: 24px; }
      .heading { flex: 1; min-width: 0; display: flex; flex-direction: column; }
      .title { font-size: 16px; font-weight: 500; line-height: 1.25; color: var(--primary-text-color);
               white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
      .subtitle { font-size: 12px; line-height: 1.3; color: var(--secondary-text-color);
                  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
      .pill { flex: none; font-size: 11px; font-weight: 500; padding: 1px 8px; border-radius: 999px;
              color: color-mix(in srgb, var(--c) 40%, var(--primary-text-color, #212121));
              background: color-mix(in srgb, var(--c) 14%, transparent); font-variant-numeric: tabular-nums; }
      .check { all: unset; cursor: pointer; flex: none; width: 26px; height: 26px; border-radius: 50%;
               display: grid; place-items: center; color: var(--secondary-text-color); }
      .check:hover { background: color-mix(in srgb, var(--secondary-text-color) 14%, transparent); color: var(--primary-text-color); }
      .check:focus-visible { outline: 2px solid var(--primary-color); outline-offset: 2px; }
      .check[aria-disabled="true"] { cursor: default; opacity: .4; background: none; color: var(--secondary-text-color); }
      .check ha-icon { --mdc-icon-size: 16px; }

      .progress { height: 4px; margin-top: 10px; border-radius: 2px; overflow: hidden;
                  background: color-mix(in srgb, var(--secondary-text-color) 22%, transparent); }
      .progress span { display: block; height: 100%; border-radius: 2px; background: var(--c); }

      .error { display: flex; gap: 8px; align-items: flex-start; margin-top: 10px; padding: 8px 10px; border-radius: 10px;
               font-size: 12px; line-height: 1.35; color: var(--primary-text-color);
               background: color-mix(in srgb, var(--hr-alert) 12%, var(--secondary-background-color, transparent)); }
      .error ha-icon { --mdc-icon-size: 18px; color: color-mix(in srgb, var(--hr-alert) 55%, var(--primary-text-color, #212121)); flex: none; }
      .error b { font-weight: 500; color: color-mix(in srgb, var(--hr-alert) 40%, var(--primary-text-color, #212121)); }
      .error span { min-width: 0; overflow-wrap: anywhere; }

      .section { margin-top: 12px; }
      .shead { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin: 0 2px 6px; min-height: 24px; }
      .stitle { font-size: 12px; font-weight: 500; color: var(--secondary-text-color);
                text-transform: uppercase; letter-spacing: .04em; }
      .stitle .count { font-variant-numeric: tabular-nums; }
      /* No filled button: a tinted outline, the accent colour for the text. */
      .install, .cbtns button { all: unset; box-sizing: border-box; cursor: pointer; flex: none; display: inline-flex; align-items: center; gap: 4px;
               font-size: 12px; font-weight: 500; line-height: 1; padding: 5px 10px; border-radius: 999px; font-variant-numeric: tabular-nums;
               color: color-mix(in srgb, var(--hr-info) 45%, var(--primary-text-color, #212121));
               border: 1px solid color-mix(in srgb, var(--hr-info) 45%, transparent); }
      .install ha-icon { --mdc-icon-size: 16px; }
      button.install:hover, .cbtns button:hover { background: color-mix(in srgb, var(--hr-info) 12%, transparent); }
      .install:focus-visible, .cbtns button:focus-visible { outline: 2px solid var(--primary-color); outline-offset: 2px; }
      .install.busy { cursor: default; border-color: transparent; color: var(--secondary-text-color); }
      .cbtns .confirm-no { color: var(--secondary-text-color); border-color: color-mix(in srgb, var(--secondary-text-color) 40%, transparent); }
      .cbtns .confirm-no:hover { background: color-mix(in srgb, var(--secondary-text-color) 12%, transparent); }

      .confirm { display: flex; flex-wrap: wrap; align-items: center; gap: 8px 10px; margin-top: 10px; padding: 8px 10px; border-radius: 10px;
                 font-size: 12px; line-height: 1.35; color: var(--primary-text-color);
                 background: color-mix(in srgb, var(--hr-info) 12%, var(--secondary-background-color, transparent)); }
      .confirm > ha-icon { --mdc-icon-size: 18px; flex: none; color: color-mix(in srgb, var(--hr-info) 55%, var(--primary-text-color, #212121)); }
      .confirm b { font-weight: 500; }
      .ctext { flex: 1 1 180px; min-width: 0; }
      .cbtns { display: flex; gap: 6px; margin-left: auto; }
      .row.busy .ic { color: color-mix(in srgb, var(--hr-info) 55%, var(--primary-text-color, #212121)); }
      .row.busy .ic ha-icon { animation: hr-pulse 1.2s ease-in-out infinite; }
      @keyframes hr-pulse { 50% { opacity: .35; } }
      @media (prefers-reduced-motion: reduce) { .row.busy .ic ha-icon { animation: none; } }
      .list { display: flex; flex-direction: column; gap: 6px; }
      .empty { font-size: 13px; color: var(--secondary-text-color); padding: 8px 10px; border-radius: 10px;
               background: var(--secondary-background-color, rgba(127,127,127,.08)); }
      .row { --t: var(--hr-info); all: unset; box-sizing: border-box; min-width: 0;
             display: flex; align-items: center; gap: 8px; padding: 5px 8px 5px 5px; border-radius: 10px;
             background: var(--secondary-background-color, rgba(127,127,127,.08)); }
      .row.warn { --t: var(--hr-warn); background: color-mix(in srgb, var(--t) 12%, var(--secondary-background-color, transparent)); }
      button.row { cursor: pointer; }
      button.row:hover { background: color-mix(in srgb, var(--t) 14%, var(--secondary-background-color, transparent)); }
      .row:focus-visible { outline: 2px solid var(--primary-color); outline-offset: 2px; }
      .ic { position: relative; flex: none; width: 28px; height: 28px; border-radius: 50%; display: grid; place-items: center;
            color: color-mix(in srgb, var(--t) 55%, var(--primary-text-color, #212121));
            background: color-mix(in srgb, var(--t) 18%, transparent); overflow: hidden; }
      .ic ha-icon { --mdc-icon-size: 16px; }
      .ic img.pic { position: absolute; inset: 5px; width: 18px; height: 18px; object-fit: contain; }
      .ic:not(.nopic) img.pic + ha-icon { visibility: hidden; }
      .ic.nopic img.pic { display: none; }
      .txt { flex: 1; display: flex; flex-direction: column; min-width: 0; }
      .name { font-size: 13px; font-weight: 500; line-height: 1.2; color: var(--primary-text-color);
              white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
      .sub { font-size: 11px; line-height: 1.2; color: var(--secondary-text-color); font-variant-numeric: tabular-nums;
             white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
      .row.warn .sub { color: color-mix(in srgb, var(--t) 40%, var(--primary-text-color, #212121)); }
      .chev { flex: none; --mdc-icon-size: 18px; color: var(--secondary-text-color); }
    `;
  }
}

// ── Editor ───────────────────────────────────────────────────────────────────
const HR_HELPERS = ['entity', 'title', 'show_updates', 'show_failed', 'check_button', 'install_button', 'hide_when_ok', 'language'];

class HacsRefreshCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = config;
    this._update();
  }

  set hass(hass) {
    this._hass = hass;
    this._update();
  }

  _update() {
    if (!this._hass || !this._config) return;
    if (!this._form) {
      this._form = document.createElement('ha-form');
      const t = (key) => hrT(hrLang(this._hass, this._config), key);
      this._form.computeLabel = (s) => t(`ed_${s.name}`);
      this._form.computeHelper = (s) => (HR_HELPERS.includes(s.name) ? t(`ed_${s.name}_helper`) : undefined);
      this._form.addEventListener('value-changed', (ev) => {
        const config = { ...ev.detail.value };
        // Options left at their default are not written to the YAML.
        for (const k of Object.keys(config)) {
          if (config[k] === '' || config[k] == null || HR_DEFAULTS[k] === config[k]) delete config[k];
        }
        this.dispatchEvent(new CustomEvent('config-changed', { detail: { config }, bubbles: true, composed: true }));
      });
      this.appendChild(this._form);
    }
    this._form.hass = this._hass;
    const c = this._config;
    const lang = hrLang(this._hass, c);
    // Reassigning the schema at every Home Assistant update would re-render ha-form while the user is typing.
    if (this._deps && this._deps.config === c && this._deps.lang === lang) return;
    this._deps = { config: c, lang };
    this._form.data = { ...HR_DEFAULTS, ...c };
    this._form.schema = [
      { name: 'entity', selector: { entity: { filter: { integration: 'hacs_refresh', domain: 'sensor', device_class: 'enum' } } } },
      { name: 'title', selector: { text: {} } },
      { name: 'show_updates', selector: { boolean: {} } },
      { name: 'show_failed', selector: { boolean: {} } },
      { name: 'check_button', selector: { boolean: {} } },
      { name: 'install_button', selector: { boolean: {} } },
      { name: 'hide_when_ok', selector: { boolean: {} } },
      {
        name: 'language',
        selector: {
          select: {
            mode: 'dropdown',
            options: [
              { value: 'en', label: 'English' },
              { value: 'fr', label: 'Français' },
              { value: 'de', label: 'Deutsch' },
              { value: 'es', label: 'Español' },
              { value: 'sr', label: 'Српски' },
              { value: 'sr-Latn', label: 'Srpski (latinica)' },
              { value: 'it', label: 'Italiano' },
              { value: 'nl', label: 'Nederlands' },
              { value: 'pt', label: 'Português (Portugal)' },
              { value: 'pl', label: 'Polski' },
            ],
          },
        },
      },
    ];
  }
}

if (!customElements.get('hacs-refresh-card')) {
  customElements.define('hacs-refresh-card', HacsRefreshCard);
  customElements.define('hacs-refresh-card-editor', HacsRefreshCardEditor);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: 'hacs-refresh-card',
    name: 'HACS Refresh Card',
    description: 'The HACS check of HACS Refresh: status, last and next check, updates available and failed repositories',
    preview: true,
    documentationURL: 'https://github.com/juju35/ha-hacs-refresh',
  });
  console.info(`%c HACS-REFRESH-CARD %c v${HACS_REFRESH_CARD_VERSION} `, 'background:#14b8a6;color:#fff;font-weight:700', '');
}
