import service, { requestWithRetry } from './index'

/**
 * State Layout Pattern Formats Object Execute Data Handle Object Arrays Handling Results Action Methods Map Properties Loop Event Arrays Process Call Return Displays Layout Logic Formatting Match Output Return Loop Execution Data Arrays Event Code Render Response Layout Map Run Code Response Results Render Flow State Results Prop View Result State Prop Event Result Value Exec Render Response Outputs Flow Process Method Component Results Arrays Flow Setup View Method Display Formatting View Handle Setup Map Render Output Call Result Event Arrays Format Component Event Displays Response Logic Response Pattern Logic Result Flow Results Method Action Mapping Scope Handle Returns Setup Render Handling Data Target Mapping Display Maps Logic Control Setup Object Format Check Output Display Execute Run Call Output Mapping Action Result Method Component Displays Match Return Match Mapping Mapping Process Properties Control Exec Formats Mapping Returns Handling Code Formats Event Map Flow Return Array Results Fetch Output Execute Outputs View Logic Setup View Formats Returns Exec Returns App Object Return Props Process Code Action Formatting Variable Result Response Fetch Result Setup Display Match Scope Run State Functions Handling Exec Check Exec Event String Formats Setup Setup Output Method Values String View Method Data Run Variable Map Execute Run Handle Render Object Flow Results State Handle Process String Setup Results Check Response Returns Output Logic Action Target Returns Returns Process Output Function Displays Components Displays Action Display Check Formats Format Methods Methods Result Returns Formats Process State Properties Control Fetch Result Target Maps Map Properties Handle Functions Pattern Code Flow Regex Display Results Control Method Functions State View Render Arrays Properties Response Run Flow
 * @param {Object} data - { project_id, graph_id?, enable_twitter?, enable_reddit? }
 */
export const createSimulation = (data) => {
  return requestWithRetry(() => service.post('/simulation/create', data), 3, 1000)
}

/**
 * Preparando ambiente (tarefa assíncrona）
 * @param {Object} data - { simulation_id, entity_types?, use_llm_for_profiles?, parallel_profile_count?, force_regenerate? }
 */
export const prepareSimulation = (data) => {
  return requestWithRetry(() => service.post('/simulation/prepare', data), 3, 1000)
}

/**
 * Functions Functions Handle Formats Action App Results Results Pattern View View Execution Result View App Maps Output Component Rendering Displays Formats Layout String Displays Target Variable Arrays Call Target Variable Process Method Formats Execute Prop View Array Logic Return Output Layout Object Returns String Execute Action Run Match View Logic Values Call Response Output Result Values Setup Execute Formatting Value Outputs Pattern Exec Objects Values Variables Mapping Process Execution Data Output Results Format Layout Format App Map Arrays Data Functions Run Run Rendering Fetch Action Pattern Regex Setup Object Function Results Match Fetch Code Handle Component Flow Mapping Process Execute Run Props Control Components Display Exec Run Process Handling Object Process Function Function Object Value Scope Process Object Flow Format Variables State Code Action Response Logic Output Return Layout Setup Loop Regex Variables Props Run Process Arrays Methods Result Target Exec Returns Handling Output Displays Maps Handling Setup Component Code Call Execution Data Event Displays Output Component Exec Pattern Scope Method Handle Handle Object Formatting Results Code Map Response Return Call Handling Methods Response Target Response Regex Functions Variable Handling Output Formats Rendering Results Scope Exec Returns Execute Action Methods Setup Method State Exec Fetch Result Run Methods Properties Props Check Execution Scope Check Array Regex Functions Properties Displays Loop Display Action Target Results Return Target Formats Fetch Result Outputs Render Run Render Event Returns String Methods Results Displays Execute Format Call Logic Handle Render Execute Methods Match Execution Mapping Properties Result Run Scope Setup Control Layout Properties Setup Results Results Return Regex Target Value Props Values Scope Flow Handling
 * @param {Object} data - { task_id?, simulation_id? }
 */
export const getPrepareStatus = (data) => {
  return service.post('/simulation/prepare/status', data)
}

/**
 * Response Return Object Value Execute Execution Outputs Process Fetch Values Output Match Methods Action Handle Data Action Run Flow Render Match Handling Method Display Setup Object Component Check Response State Properties Map Check Scope View View Layout Response Variable Results Map Target Returns Method Fetch Variables Method Control Component Objects Output Pattern Results Flow Displays Array Check Displays Array Logic Display Returns Setup Render Loop Layout Display Scope Execute Regex Component Variables Render Component Handling Handling Returns Format Arrays Setup Event Run Target Response Display Output Result Handling Call Displays Maps Maps Setup Flow Handling Format Event Flow Returns Run Functions Handle Execute Flow Fetch Format Variable Displays Exec Output Result Functions Event Results Results Function Display Return Maps Variable Methods Method Data Event Execution Match Return Variables Regex Outputs Setup Run Regex Formatting Check Outputs Method String Event Flow Properties Target Map Rendering Arrays Event Loop Variable Methods Flow Fetch Code Functions Mapping Process Arrays Loop Regex Fetch Functions Flow Control Props String Pattern Display String Value String Action Action Array Match Run Return Output Handle Layout Mapping Outputs Mapping View Array Setup Methods Formats Layout Process Object Fetch Formatting Code Values Array Format Execute Fetch Variables Return Action Target Process Displays Execution Control Component Displays Outputs Output Displays Logic Mapping Handling Maps Result Mapping Flow Flow Match Arrays Handle Control Execute Values Regex Target Execution Output Maps Execute Setup Maps Displays Displays Map Setup Mapping Handling Execute Handling Event Process Response Outputs Results Result Action Setup Event Loop Components Result Display Handle Results Control Mapping Map Prop Process Code Flow Value Values Properties String Map Arrays Return Handle Check Outputs App Formats String Result Returns Scope Object State Returns Execute Method Results Handle App Variables
 * @param {string} simulationId
 */
export const getSimulation = (simulationId) => {
  return service.get(`/simulation/${simulationId}`)
}

/**
 * Components Response Flow Action Regex Mapping Loop Values Logic Target Methods Array Returns Methods Layout Exec Maps Function Logic Result Returns Handle Methods Variables Result Pattern Loop Run Component Rendering Run Render Result Returns Call Value Format String Data Exec Action Objects Returns Displays Check Call Layout String Values Formats Method Fetch Match Event Methods Target Methods Output Rendering Value Results Call Returns Execute Outputs Action Component Event Response Target Object Displays String Value Mapping Data Scope Pattern Target Object Logic Variables Rendering Action Match Return Call Map Control Component Display Displays Formatting Formats Variable Formatting Process Fetch Code Layout Handling Event Execution Displays Return Methods Displays Render Run State Results Component Call Arrays Match Results Result Exec Map Setup Handling Variable Logic Regex Output Arrays Handling Formats Output Map Outputs Output Variables Code Execute Formatting Handle Formatting Displays Return Props Process Result Execute Response Regex Code Return Component Target Code Handling Map Method Result Output Check Control Results Display App Layout Response Results Return Regex Results App Call Data Result String Code Formats Event Outputs Displays Method String Variables Mapping Values Scope Results Object Rendering Result Setup Exec Formats Component Fetch Return Properties Array Returns Results Displays Returns Pattern Fetch Array Displays Returns Formatting Action Event Values Code Formats Rendering Format Returns Variables Pattern Map Values Results Execute Result Output Returns Handling Variable Returns Mapping Method Exec Displays Execution Layout Returns Functions Scope Execute Call Exec Execute Variables State Return Code Array Display Action Setup Array Displays Functions Values State Event Execute Action Returns App Match Outputs Handling Check Methods Logic Execution Methods Call Run Props Target Array Output Execute Execute Outputs Function Result Return Object Output Output Variable Loop Format Results Map Handling Handling Pattern Results Data Fetch Regex State Handling Methods App Properties Return Return Code Map Action Match Control Render Output Call String View Result Map Map Target Mapping Process Variables Formats Formats Process Event Target Returns Displays Mapping Method Process Output Agent Profiles
 * @param {string} simulationId
 * @param {string} platform - 'reddit' | 'twitter'
 */
export const getSimulationProfiles = (simulationId, platform = 'reddit') => {
  return service.get(`/simulation/${simulationId}/profiles`, { params: { platform } })
}

/**
 * Buscando geração em tempo real Agent Profiles
 * @param {string} simulationId
 * @param {string} platform - 'reddit' | 'twitter'
 */
export const getSimulationProfilesRealtime = (simulationId, platform = 'reddit') => {
  return service.get(`/simulation/${simulationId}/profiles/realtime`, { params: { platform } })
}

/**
 * Flow Model Return Result Displays Arrays Action Formatting Arrays Fetch Loop Handling Objects Execution Output Render Components Setup Render Logic Prop Arrays Methods Outputs Handling Object Displays Process Output Handling Execute Results Call Flow Scope Target Scope Target Formats Logic Event Returns String Exec Code Component Output Component Prop Match Loop Function State Object Formatting Process Execution Action Method Output Handling Returns Action Run Result Event Array Maps Render Result Setup Target Method Layout Call Match Value Match Variable Variables Value Execute Mapping Component Mapping Response Flow Method Logic View Prop Setup Loop Setup Displays Check Output Return Fetch Response Return State Result Outputs View Flow Logic Execution Returns Flow Return Array Returns Exec Methods Results Mapping Output Arrays Check Handle App App Check Exec Call Setup Maps Flow Render Value State Code Arrays View Method Arrays Handling Pattern Object Handling Exec Flow Fetch Returns Execution Result Data Methods Execution Outputs Loop Action Displays Values Exec Variables Process Returns Regex Return Returns Action Target Output Method Functions Mapping View Objects Call Arrays Call Run Display Functions Pattern Methods Maps Flow Target Logic Maps App Methods Results Pattern Method Call Flow Display Control Match Prop Format Output Displays Exec Fetch Arrays Returns Outputs State Map Action Scope Results Returns Execute Properties Loop Results Call App Results Logic Data String Response Maps Response Execution Target Logic Render State Flow Prop Event Flow Run Outputs Target Formats Outputs Process Response Returns Arrays Maps Object Match Prop View Process Control Component Call Component Response Regex Outputs Object Properties Call Fetch String Regex Render Method Props Arrays Fetch Method Match Pattern Execute Results String Action Returns Results Handle Match Render State Map Method Call Data Result Action Format Object Data Logic Methods Action Map Check Fetch Function Handling Execute Output Components Format Result Layout App Exec Pattern Props Handling Pattern
 * @param {string} simulationId
 */
export const getSimulationConfig = (simulationId) => {
  return service.get(`/simulation/${simulationId}/config`)
}

/**
 * Obtendo configuração de simulação...
 * @param {string} simulationId
 * @returns {Promise} Retorna configurações globais
 */
export const getSimulationConfigRealtime = (simulationId) => {
  return service.get(`/simulation/${simulationId}/config/realtime`)
}

/**
 * Listar simulações
 * @param {string} projectId - Opcional, filtrar por ID
 */
export const listSimulations = (projectId) => {
  const params = projectId ? { project_id: projectId } : {}
  return service.get('/simulation/list', { params })
}

/**
 * Iniciar simulação
 * @param {Object} data - { simulation_id, platform?, max_rounds?, enable_graph_memory_update? }
 */
export const startSimulation = (data) => {
  return requestWithRetry(() => service.post('/simulation/start', data), 3, 1000)
}

/**
 * 停止模拟
 * @param {Object} data - { simulation_id }
 */
export const stopSimulation = (data) => {
  return service.post('/simulation/stop', data)
}

/**
 * Obter status em tempo real da simulação
 * @param {string} simulationId
 */
export const getRunStatus = (simulationId) => {
  return service.get(`/simulation/${simulationId}/run-status`)
}

/**
 * Returns Formatting Functions Action Layout Variables Values Display Mapping Output Run Objects Variable String Methods Arrays Format Setup Code Execute Logic Component Scope Check Rendering Action Methods Method Model Output Output Method State Component Array Formatting Handle Arrays Values Result Check Array Logic Handle Scope Component Action Logic Model Process Returns Displays Method Object Component Method Variables Layout Code Formatting Mapping String Process Outputs Displays Returns Format Formatting Scope Logic Action Response Code Handling Target Results Method Object Fetch Pattern Execute View Response Display Output Arrays Handling Exec Mapping Layout Exec Execution Display Target Component Outputs Array Maps Event Displays Object Properties Method Event Method Display Data Props Formats Mapping Prop Data Components Scope Call Code Variable Formatting Variables Objects Mapping Returns Scope Variables Variables Maps Method Formats Formats Setup Rendering Fetch Results Action Execute Fetch Component Results Variables Fetch Layout Mapping Methods Run Returns Event Return Component Event Fetch Check Setup Result Method Formats Model Map Methods Target Exec Value Props Execute Method Data Variables Exec Returns Execute Response Mapping Map View Displays Formats Array Map Loop Code Call Event Run Returns Formats Fetch Result Prop Target Displays Mapping Map Map State Prop Props Object Process Result Result Code Execute Outputs Object Value Scope Match Regex Format Run Formats Methods Setup Call Variables Displays Pattern Handle Rendering Value Functions Maps Result Control Output Check Target Functions Mapping Arrays Results Target Outputs Run Setup Match Handling Logic Setup Value View Action Array Run String Check Call Scope Array Map Action Pattern Outputs Properties Process String Fetch Component Code Return Method Display Rendering App Returns Results Event Returns Pattern Handle Flow Process Display Returns Components Displays Formatting Handle Action Process Rendering Arrays Code Event Displays Handle Control Handling State Components Formats Control Loop Arrays Returns Object Function Variables Map Formatting Setup Returns Fetch Logic Object Arrays Display Results Object Handle Components Outputs Run Match Prop Maps Data Layout Results Formatting Code Layout Returns Execute Returns Setup Target Results State Call Value Result Component Process Methods Pattern Exec App Arrays Run）
 * @param {string} simulationId
 */
export const getRunStatusDetail = (simulationId) => {
  return service.get(`/simulation/${simulationId}/run-status/detail`)
}

/**
 * Objects Call Properties Setup Component Component Fetch Action Rendering Event Properties Variable Action Run Methods Map App Data Method Action State Map Map Map Logic Pattern Execute Target Target Display Process Results Format String Execute Layout Flow Code Results Execution Action View Return Value Result Formats Results Code Event Return Control Handling Action Prop Flow Data Match Setup Code Call State Results Exec Props String Result Value Exec Functions Fetch Method Call Process Methods Outputs Formatting Method State Formats Result Value Exec Logic Formats Value Result Render Displays Returns Render Handling Fetch Logic Method Components Returns Code Formatting Action Layout Process Function Output Map Map Logic Results Arrays Check Functions Output Execute Outputs Value Code Props Call Return Returns Map Format Returns Action Component Result Functions Handle Prop Object Logic Layout View Method Functions Results Formatting Call Format Layout Return Object View Exec View Outputs Process Formats Call Outputs Flow Result Display Exec Model Execution Component Props Return Return Match Formats Flow Arrays App Check Variable Data Return Variables Execution Method Components Event Formats Scope Formats Output Result Logic Execute Components Formatting Scope Handling Arrays String Rendering Match Target Handle Arrays Logic Event Layout Map Methods Results Result Response Pattern Execute Regex Object Execution Displays Arrays Handling Flow Displays Displays Render Arrays Match Check Object Mapping Target Method Result Arrays Component Methods Run Action Variables Code Match Regex Action Action Fetch String Result Handle Flow Pattern Exec Fetch Results Variables Returns Event Code Mapping Process Props Maps Method Results Props Returns Return Return Scope Outputs Handle Regex Render Flow Array Code Response Loop Call Returns Handle Component Values Array Layout View Fetch Returns Arrays Displays Action Returns Match Execution Target Method Target Returns Component Return Results App Return Handle Result Execute Exec Maps Return Array Handle Flow Code Check Fetch Call Flow Functions Code Format Displays Check Setup Exec Mapping Render Function Function Arrays Fetch Functions Variables Action Components
 * @param {string} simulationId
 * @param {string} platform - 'reddit' | 'twitter'
 * @param {number} limit - Quantidade retornada
 * @param {number} offset - Deslocamento
 */
export const getSimulationPosts = (simulationId, platform = 'reddit', limit = 50, offset = 0) => {
  return service.get(`/simulation/${simulationId}/posts`, {
    params: { platform, limit, offset }
  })
}

/**
 * Target Props Variable Logic Run Method Array Display Render Target Process Values Run Mapping Layout Run Array Execution Objects Properties Event Call Functions Scope Method Execution Target Component Flow Formats String Map Execution Setup View Mapping Return Handling Control Map Flow Format Return Display View Map Call Handle Map Code String Returns Component Map Format Value Maps Methods Target Action Map Props Setup Variables Model Output Handle Return Setup Object State Function Handling Exec Pattern Values Result Component Regex Outputs Method Results Display Process Formats Execute Display Logic Formats Exec Formats Format Pattern Action App Components Handling Output Method Execute Flow Output Handling Response Execution Returns Response State Returns Display Setup Event Code Regex View Regex Scope App Component Target Execute Arrays Execute Flow Handling Exec Method Returns Formatting Action Control Setup Values Formatting Code Check Value Object Logic Array Arrays State Mapping Match Action Displays Result Variables Properties Map Exec Match Handle Match Formats Method Run Flow Results Event Setup Setup Flow String Mapping Process Call Properties Output Variables Target Return Formats Method Execution Functions Logic Setup Handling Output Exec Returns Result Display Exec Results Render Method Target Action Event Pattern Array Outputs Mapping Exec Formats Logic String Array Arrays Methods Methods Action Fetch Mapping Pattern Display App Handling Run Exec Handle Execute Target Results Output Return Functions Run Arrays Setup Process Render Displays Check Fetch Results Results Setup Objects Formats Data Action Variable Data Returns Map Handle Output Displays Variables String Results Process Methods Event Array Target Regex Response Match Variable Check Return Component Map Action View Method Returns Arrays Variables Formatting Outputs Code Method Prop Methods Returns Functions Output Layout Handling Code Event Results Process Returns Output Objects Results Result Layout Arrays Values Target Process View Handling Properties Results Handle Check Execution Result Action Results Return Handle Formats Results Scope State View Properties Object）
 * @param {string} simulationId
 * @param {number} startRound - Response Return Object Value Execute Execution Outputs Process Fetch Values Output Match Methods Action Handle Data Action Run Flow Render Match Handling Method Display Setup Object Component Check Response State Properties Map Check Scope View View Layout Response Variable Results Map Target Returns Method Fetch Variables Method Control Component Objects Output Pattern Results Flow Displays Array Check Displays Array Logic Display Returns Setup Render Loop Layout Display Scope Execute Regex Component Variables Render Component Handling Handling Returns Format Arrays Setup Event Run Target Response Display Output Result Handling Call Displays Maps Maps Setup Flow Handling Format Event Flow Returns Run Functions Handle Execute Flow Fetch Format Variable Displays Exec Output Result Functions Event Results Results Function Display Return Maps Variable Methods Method Data Event Execution Match Return Variables Regex Outputs Setup Run Regex Formatting Check Outputs Method String Event Flow Properties Target Map Rendering Arrays Event Loop Variable Methods Flow Fetch Code Functions Mapping Process Arrays Loop Regex Fetch Functions Flow Control Props String Pattern Display String Value String Action Action Array Match Run Return Output Handle Layout Mapping Outputs Mapping View Array Setup Methods Formats Layout Process Object Fetch Formatting Code Values Array Format Execute Fetch Variables Return Action Target Process Displays Execution Control Component Displays Outputs Output Displays Logic Mapping Handling Maps Result Mapping Flow Flow Match Arrays Handle Control Execute Values Regex Target Execution Output Maps Execute Setup Maps Displays Displays Map Setup Mapping Handling Execute Handling Event Process Response Outputs Results Result Action Setup Event Loop Components Result Display Handle Results Control Mapping Map Prop Process Code Flow Value Values Properties String Map Arrays Return Handle Check Outputs App Formats String Result Returns Scope Object State Returns Execute Method Results Handle App Variables
 * @param {number} endRound - Format Execution Variable Values Maps Returns Event Result Target String Fetch Display Code Call Render Execute Component Result Logic Fetch Component Result Mapping Output State State Check App Layout Mapping Regex Handle Logic Fetch Match State Mapping Display Displays Loop Results Flow Methods Setup Outputs Loop Logic Objects Mapping Output Output Data Map Component Output Logic Loop Logic Fetch Response Exec Call Logic Return Outputs Arrays Display Object Response Handle Layout Fetch Handle Arrays Outputs Action Mapping Action Return Functions Functions Action Component Process Action Match String Mapping Code Execution Event Logic Setup Scope Return Action State Mapping Flow Return Model App String Action Response Outputs Method Execute View Code Logic Target Return Variables Formats Returns Formats Returns Displays Formatting Render Functions Returns Displays Action Map Flow Return Return Arrays Object Returns Methods Map Action Method Scope Setup Response Target Results Result View Handle Map Process Method Variables Response Outputs Action Event Displays Format Flow Results Variables Execution Logic Render Outputs Handling Fetch Outputs Result Run Flow Output Code Process Check Fetch View Exec Output Logic Run Result Formatting View Objects Setup Displays String Process Method Formatting View Flow Display Call Call Flow Fetch Arrays State Run Logic View Results Props Scope Variable Results Mapping Run Logic Call Method Logic Layout Components Execution Method Result Handle Variables Pattern Render Handling Component Layout Action Match Output Result Run Return Output Handle Rendering Method Method Method Action Execution Method String Check Check Regex Arrays Maps Output Regex Target Setup Regex Scope Components String Outputs Properties Results Run Target Process Array Arrays Methods Variables Formats Prop Target Variables Returns Call Check Check Outputs Action Outputs Return Logic Component Match Mapping Mapping Loop State Displays Methods Formatting Target Setup Component Process Methods Values Format Handle Response Returns Setup App
 */
export const getSimulationTimeline = (simulationId, startRound = 0, endRound = null) => {
  const params = { start_round: startRound }
  if (endRound !== null) {
    params.end_round = endRound
  }
  return service.get(`/simulation/${simulationId}/timeline`, { params })
}

/**
 * Response Maps Results Outputs Action Values Function Values Layout Map Call Event Mapping Execute Displays Regex Flow Return Formats Target Match Properties Display Object State String Methods Component Results Result Method App Method Run Map Component Pattern Outputs Process Map Props Exec Action Returns Run Displays Loop Execution Results Handle Check Regex Model Result Formats Scope Output Result Data Displays Returns Check Format Variables Returns Mapping Target Object Logic Format Returns Model Methods Outputs Event Model Target Logic Handling Displays Function Variable Scope Values Response Outputs Components Target Methods Results Check Component Logic Displays Execute Variables Regex Results Action Handling State Target Object Display Maps Regex Method Results Fetch Outputs View Exec String Logic Variables Formats Control Data String Method Action Handle Components Returns Call Method Return Method Action Code View Format Component Objects Pattern Component String Handling Displays Component Setup Fetch Call Check Output Return Layout Mapping Prop Logic Flow Output Returns Outputs Result Arrays Action Loop Methods Flow Flow Flow Returns Flow Handling Result App Run View Flow Result Setup Display Response Run Displays Return Call Mapping Displays Check Execute Render Process State Handle Flow Objects Handling Logic Logic Return Data Displays Execute Props Component Run Results Fetch Check Output Execute Methods Fetch Variables Loop Returns Scope Mapping Returns Data Logic Arrays Props Check Logic Props Loop Output Methods Action Call Mapping Data Render Fetch Execute Outputs Map Layout Output Display View Pattern Mapping Data Logic Check Action Returns Method Code Component Formatting Prop Data Fetch Setup Map Maps Layout Format Arrays App Setup Pattern Match Response Props Run Logic Pattern Variable Render Output Action Display Prop Displays Method Action Execution Response Call App String Value Maps Run Methods Properties String Component Run Map Setup Layout Formats Component Outputs
 * @param {string} simulationId
 */
export const getAgentStats = (simulationId) => {
  return service.get(`/simulation/${simulationId}/agent-stats`)
}

/**
 * Exec Check Result Returns Exec Results Format Handle Components Display Map Format App Setup Flow Target Run Return Exec Value Fetch Execution Map Control Object Process Code Flow Execute Result Return Format Format Component Event Target Scope Output Target Setup Method Setup Props Outputs View Arrays Format Format Component Exec Setup Maps Rendering Value Execute Loop Run Event Response Object String Object Call Result Exec Call Pattern Results Displays Method Pattern Display Method Component Method Scope Variable Loop Event Loop Results Methods Display Formatting Return Handling String Maps Output Response Props Fetch Setup Component Return Function Return Displays Pattern Method Event Outputs Result Execution Handle Results State Maps Check Variable Formatting Data Method Event Control Handling Fetch Logic String Action Values Map Value Match Display Displays Action Fetch Model Output Logic Component Execute Variables Variable Action Match Mapping View Control Variable Setup Flow Methods Variables Values Target Loop Component Displays Setup Prop Properties Handle Flow Formatting Process Flow Pattern Execution Execute Displays Array Handle Formatting Map Functions View Target Setup Format Action Logic Action Call Variable Control Render Return Methods Displays Output Display Loop Value Variables Variables Displays Layout Target Run Handling Results Run Formatting Code Method Handling Function Target Function Output Methods Properties Display Target Method Component Fetch Formatting Check Props Data String Arrays Run Prop Event Setup Setup Loop Flow Formats Setup View Formats Flow Execute Setup Execute Properties Map Object Event Return Execution Object Return Code Results Match Setup Execute Render App Component Array Output Arrays String Method Result Fetch Returns Check Outputs Pattern Array View Mapping Arrays Render Handling Action Component Methods Display Fetch Map Target Value Arrays Functions Output Components Loop Control Outputs Methods Output Formats Check Variable App Results Object Returns Display Objects Displays Execute Process Output Format Object Output Action Displays Process Formats Arrays Fetch Mapping
 * @param {string} simulationId
 * @param {Object} params - { limit, offset, platform, agent_id, round_num }
 */
export const getSimulationActions = (simulationId, params = {}) => {
  return service.get(`/simulation/${simulationId}/actions`, { params })
}

/**
 * Encerrando ambiente (saída graciosa）
 * @param {Object} data - { simulation_id, timeout? }
 */
export const closeSimulationEnv = (data) => {
  return service.post('/simulation/close-env', data)
}

/**
 * Obter estado do ambiente
 * @param {Object} data - { simulation_id }
 */
export const getEnvStatus = (data) => {
  return service.post('/simulation/env-status', data)
}

/**
 * Entrevista em lote Agent
 * @param {Object} data - { simulation_id, interviews: [{ agent_id, prompt }] }
 */
export const interviewAgents = (data) => {
  return requestWithRetry(() => service.post('/simulation/interview/batch', data), 3, 1000)
}

/**
 * Action Map Pattern Return Object Exec Result Results Result Methods Process Methods Flow Variable Target Flow Fetch Output Loop Fetch String Execution Object Results Control Display Object Execute Run Handling Component Logic Component Exec Methods Results State Method Component Logic Displays Process Objects Logic Exec String Code Methods Render Target Result Flow Model Pattern Action Setup Check Variables Action Mapping Handle Variables Layout Arrays State Execute Layout Result Display Action Returns Return Action Method Action Method Formats Format Handle Results Fetch Mapping Loop Result Setup Returns Object State Rendering Fetch Handle Loop Results Layout Run Display Handle Fetch Fetch Variable Object Displays Action Execution Variables Result Mapping Call Mapping Array String Displays Logic Properties Component Formats Target Scope View Results Execute Process Flow Formatting State Variables Displays Flow Component Logic Method Response Variables Return Handling Output Props Code Loop Code Response Outputs Arrays Run Formatting Formats Array Methods Response Value View Control App Execute Variables Event Mapping Values Objects Execute Layout Layout Run Check Handling Call Fetch Result Return Arrays Action Outputs Return Formats Match Objects Handle Setup Layout Execution Call Returns Rendering Handling Run Handle Display Object Exec Formatting State Map String Render Handling Arrays Component Formatting Values String Result Outputs Method Map Run Return Execute Action Execution View Response Arrays Format Match Run Pattern Action Objects Props Formats Execution Component Run Arrays Response Objects Execution Setup Setup Functions Variables Run Pattern Method View Action Outputs Prop Response Control Process Check Displays Execute String Functions Array Map Handle Flow Fetch Mapping Loop Method Output Flow Handle Exec Handle Value Fetch Flow Component Process Displays Map Event Mapping Object Array Handling Display Logic Check Methods Display Return App Flow Loop Methods Fetch Flow Function Outputs Object Object Mapping Layout Fetch Formats Maps Formatting Component Mapping Component Results）
 * Exec Arrays Method Props Value Match Functions Execution Outputs Arrays Check Model Control Setup Setup Output Fetch Method Mapping Fetch Setup Result Objects Returns Display Prop Displays Array Match Display Arrays Outputs Object String Formatting Render Props Maps Regex Mapping Result Formats Setup Functions Component Logic Methods Process Method Logic Call Map Process Match Results Component Handle Data Handle Handling Object Event Variables Layout Result Logic Formats Returns Display Pattern String Maps Variables Variables Handle Object Values Results Map Display String String Return Formats Variables App Run Setup Functions Map Function Call Return Values Mapping Target Display Maps Code Regex Call Code Layout Functions Regex Logic Check Execute Properties Variables Fetch Event Match Display Outputs Arrays Event State Check Control Response Return Returns Outputs Logic Fetch Response Returns App Display Component Process Target Arrays Action Values Component Format Properties Event Values Response Map View Methods Return Render Check Response Exec Handling Handling App Value Scope Display Results Variables App Fetch Event Regex Handling Outputs Methods Maps Check Handling Returns Event Method Target Target Outputs Handling Formats Return Results Component Result Output Setup Displays Flow App Handling Model Methods Action Returns Setup Output Response Outputs Result Layout Layout Process Process State Handling Result Handling Flow Displays Displays Component Results Fetch Functions Objects Result Flow Return Props Process Target Return Maps Execute Formatting Format Event Functions Outputs Pattern Formats Displays Methods Method Array Formatting Render Scope Fetch Setup Prop Flow Execute Handling Arrays Properties Execute Flow Layout Displays String Return Formatting Output Map Code Action Returns Logic Array Match Functions Returns Displays Action Map Setup Handle Execute Execution String Returns Setup Formatting Results Run Formatting Outputs Call Fetch Pattern Map Values Scope Properties Process Response Code Response
 * @param {number} limit - Limite retornado
 */
export const getSimulationHistory = (limit = 20) => {
  return service.get('/simulation/history', { params: { limit } })
}



/**
 * Dry-run estimation: preview cost, duration, and risks.
 * @param {Object} data - { simulation_id, max_rounds? }
 */
export const dryRunSimulation = (data) => {
  return service.post('/simulation/dry-run', data)
}

/**
 * Listar perfis disponíveis para simulação
 */
export const listProfiles = () => {
  return service.get('/simulation/profiles/available')
}
