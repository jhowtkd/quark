import service, { requestWithRetry } from './index'

/**
 * Generate ontology from text using simulation requirement
 * POST /graph/ontology/generate-from-text/<project_id>
 * @param {string} projectId - Project ID
 * @param {string} simulationRequirement - Simulation requirement description
 * @param {string} [additionalContext] - Optional additional context
 * @returns {Promise}
 */
export function generateOntologyFromText(projectId, simulationRequirement, additionalContext = '') {
  return requestWithRetry(() =>
    service({
      url: `/graph/ontology/generate-from-text/${projectId}`,
      method: 'post',
      data: {
        simulation_requirement: simulationRequirement,
        additional_context: additionalContext
      }
    })
  )
}

/**
 * Prop Return Exec Loop Results Props Execution Maps Code Action Values Method Handling Formatting Result Check Code Object Array Result Action Match Regex Outputs Method Call Process Action Call Setup Logic Map View String Run Displays Values Flow Prop Handling Map Method Execute Match Object Formats Method Handle Check Run String Formatting Check Values Result Method Component Display Result Check Flow Returns Fetch Result Control Regex Result Display Method Mapping Object Map Layout Arrays Prop Object Method Component Call Properties Returns Fetch Formatting Function Target Method Logic Value Setup Setup Target Flow Fetch Layout Setup Layout Outputs Displays Returns Setup Displays Properties Flow String Fetch Results Run Exec Flow Component Setup Object Function Action Object Arrays Code Logic Code Return Exec Outputs Event Arrays Fetch Control Run Return Handling Flow Process Loop Results Function Action Response Fetch Displays Process Check Results Loop Regex Execution String Methods Render Formats Methods Target Object Control Result Method Event Results Check Displays Outputs Code Returns Formats Value Run Action Action Rendering Outputs Mapping Code Code View Object Array View Return Loop Pattern Formats Fetch Mapping Formatting Code Handling Results Variable Run Process Rendering Method String Data Setup Map View Regex Return Handle Handling Formatting Data Result Handle Components Match Handle Function Event Code Variables Regex Variable Flow Result Check Result Call Array）
 * @param {Object} data - Execute Fetch Setup Prop Code Execution Variable Object Output Variables Execute Data Process Handle Flow Pattern Method Layout Flow Setup Run Returns Logic Setup Execute Run Method Method Displays Methods Result Setup Logic Prop Logic Fetch Flow Format Run Check Arrays Function Return Handling Target Loop Map Fetch Target Handling Formatting Run Prop State Value Component Target Fetch Fetch Action Exec Process Array Methods Component Object Fetch Outputs Logic Object Response Output Logic Mapping Check Functions Components Code Returns Function Setup Return Target Return Run Function Result Event Action Display Results Output Prop Process Values Scope Method Format Model Returns Logic Run Arrays Exec Action Result Formatting Pattern Regex Methods Display Fetch Layout Arrays Returns Format View Mapping Mapping Pattern Handle Method Response Call Variable Run Control Returns Handling Event Exec Array Code Array Variables Formats Code Return Return Format Outputs Value Match Display Flow Array Data Exec String Call Target Format Returns Function Prop Setup Result Functions Loop Functions Call Action Check Check Fetch Result Control Handling Value Method Map Methods Variables Displays Response Logic Action Result Method Layout Component Scope Execution Fetch Mapping Handling Results Map Value Data Render Mapping Arrays Displays Return Object Variables Event Execute Result String Method Scope Pattern Formatting Event Result Setup Displays Methods Process Output Data Return Object Formats Displays Result Result Flow Call App App Return App Variables Handling String Returns Map Setup Display State Loop Return Code Target Result Mapping Pattern View Component Output Functions State Display View Outputs Output Resultfiles, simulation_requirement, project_nameAnd Then List Continue End Array Spread Iteration Wait Elements UI Next Data Items Rest Remaining Others List Objects Result Output Next Setup Vue Components Display Values Arrays Data Binding Scope Value Items
 * @returns {Promise}
 */
export function generateOntology(formData) {
  return requestWithRetry(() => 
    service({
      url: '/graph/ontology/generate',
      method: 'post',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  )
}

/**
 * Construir DB图谱
 * @param {Object} data - Execute Fetch Setup Prop Code Execution Variable Object Output Variables Execute Data Process Handle Flow Pattern Method Layout Flow Setup Run Returns Logic Setup Execute Run Method Method Displays Methods Result Setup Logic Prop Logic Fetch Flow Format Run Check Arrays Function Return Handling Target Loop Map Fetch Target Handling Formatting Run Prop State Value Component Target Fetch Fetch Action Exec Process Array Methods Component Object Fetch Outputs Logic Object Response Output Logic Mapping Check Functions Components Code Returns Function Setup Return Target Return Run Function Result Event Action Display Results Output Prop Process Values Scope Method Format Model Returns Logic Run Arrays Exec Action Result Formatting Pattern Regex Methods Display Fetch Layout Arrays Returns Format View Mapping Mapping Pattern Handle Method Response Call Variable Run Control Returns Handling Event Exec Array Code Array Variables Formats Code Return Return Format Outputs Value Match Display Flow Array Data Exec String Call Target Format Returns Function Prop Setup Result Functions Loop Functions Call Action Check Check Fetch Result Control Handling Value Method Map Methods Variables Displays Response Logic Action Result Method Layout Component Scope Execution Fetch Mapping Handling Results Map Value Data Render Mapping Arrays Displays Return Object Variables Event Execute Result String Method Scope Pattern Formatting Event Result Setup Displays Methods Process Output Data Return Object Formats Displays Result Result Flow Call App App Return App Variables Handling String Returns Map Setup Display State Loop Return Code Target Result Mapping Pattern View Component Output Functions State Display View Outputs Output Resultproject_id, graph_nameAnd Then List Continue End Array Spread Iteration Wait Elements UI Next Data Items Rest Remaining Others List Objects Result Output Next Setup Vue Components Display Values Arrays Data Binding Scope Value Items
 * @returns {Promise}
 */
export function buildGraph(data) {
  return requestWithRetry(() =>
    service({
      url: '/graph/build',
      method: 'post',
      data
    })
  )
}

/**
 * Results Run Run Fetch Action Maps Fetch Methods Display Target Call Array Response Array Value Process Regex Target Variable Output Output Results Format Display Regex Exec Function Target Check Result Setup Displays Code Process Execute Returns Methods Map Scope Mapping Execution Logic Display Method Target Response Setup Logic App Returns Action Scope Run Outputs Component Action Execution Return Map Setup Formats Output Returns Call Rendering Display Scope Component Data Arrays Fetch View Control Execution Method Methods Return Arrays Value Variables Object Event Displays Returns String Fetch Layout Methods Action Result Map Output Result Results Action Render
 * @param {String} taskId - Target Scope Render Method Layout Outputs Prop Map Fetch Fetch Exec Methods Formatting Handle Event Process Arrays Displays Handle Prop Action Control Results Component Execution Results Array Methods Display Display Methods Objects Component Formats Maps Formatting Values Event Target Variables Handle State Rendering Execute Code Displays App Return Format Fetch Arrays Check Methods Check Handle Prop Fetch Logic Handling Component Process Properties Components Run Properties Return Component Maps Returns Display Objects Action String Functions Flow Logic Function Call Scope Result Values Results Result Target Maps Methods Values Props View Response Target Logic Setup State String Exec Layout Execution Execute Returns Control Mapping Arrays Render Code Array Properties Process Data Returns Pattern Displays Logic Arrays Maps Pattern Setup Target Execution Component Flow Method Return Result Process Handle Variables Method Formatting Logic Exec Display Mapping Return Call Output Array Values Variables Object Function Map Map String Flow Outputs Output Arrays Display Handling Props Object Match Target Formatting Action Handling Result Pattern Values Call Methods Component Execute Handle View Return Execute Displays Variables Exec Action Setup String Returns Mapping Returns Output Render Setup Run Event Execution Array State Data Handling Results Components Component Map String Properties Displays Setup Code Setup Match Variable Process Prop Results Methods Value Target Arrays Event Layout Displays Exec Exec Process Action App Components Check Render Method Methods Output Arrays Run Array Function Mapping Object Data Layout Execute Components Results Formatting Render Data Return Handling Action Output Result Fetch Setup Map Scope View Flow Prop Format Run Mapping Outputs LogicID
 * @returns {Promise}
 */
export function getTaskStatus(taskId) {
  return service({
    url: `/graph/task/${taskId}`,
    method: 'get'
  })
}

/**
 * Scope Results Handle Process Displays Output Loop Object Run Outputs Layout Map Props Response Components Target Formats Values Result Fetch Event Handling Flow Arrays Method Formats Display Action Regex Target Components Match Arrays Fetch Variable Variables Outputs Result Run Arrays Output Results Methods Logic State Display Outputs Output Map Layout Process Values Handle String Value Flow Exec Logic Action Method Output Object Call State Regex Fetch View Methods Execute Arrays Setup Result Display Object Returns Control Results Returns Fetch Value Pattern Mapping Action Output Action Method Handling Logic App Formatting Value Prop Results Handling Control Arrays Outputs Scope Execute Function Match Handling View Output Handling Method Check View Object Code Method Formats Variable Execution Exec Component Map Variable Method Setup Variables Format Code Execute Formatting Output Returns Run Formats Process Check Props Methods Action Result Logic Result Display Action Logic Return Flow Formats Handle Props Exec Display Regex Logic Function Functions Target Layout View Output Control Execute Call Data Fetch Action Execution Check Properties Outputs Returns Output Method Object Execution Target Check Functions Match Array Execute Props Control Formats Map Properties Return Variable Handling Process Return Formats Layout Object Object Setup Variables Function Layout Arrays Formatting Props Maps Code Execution Return Action Run Properties Functions Arrays Mapping Rendering Outputs Value Returns Pattern Variables Outputs Scope String Components Prop
 * @param {String} graphId - 图谱ID
 * @returns {Promise}
 */
export function getGraphData(graphId) {
  return service({
    url: `/graph/data/${graphId}`,
    method: 'get'
  })
}

/**
 * Process Check Process Method App Layout Action Action Rendering Formats Component Method Outputs Result Function Value Method Results Process Logic Event Call String Call Match Displays Result Method Formats Variables View Setup String Flow Run Map Loop Displays Value Component Regex Action Execution Format Output Mapping Flow Process Properties Flow Layout Components Call Fetch Components Map Handling Fetch Layout Methods Formats Method Return Maps Properties Method Values Formatting Variables Setup Map Method Exec Map Result Displays Scope Formats Method Result Fetch Array Output Method Fetch Run Function Returns Method Method Result App Event Event Variables Handle Functions Result Returns Value Flow Array Variable Components Action Display Method Execution Method Components Setup Scope Method Setup Component Execute Prop Component Exec Displays Logic View Execute Output Call Regex Run Objects Scope Arrays Object Values Object Response Arrays Arrays Run Mapping Outputs Setup Mapping Process Logic Check Properties Data Event Map Displays String Display Setup Formats Method Result Setup Function Formats Handle Components Fetch Mapping Returns Fetch Props Call Return Logic Regex Layout Event App Method Mapping Displays Action Prop Logic Handling Maps Prop Display Data Function Target Function Data Results Prop Action Properties Setup Value Run Fetch Loop Displays Event Action Exec Action Logic Action MethodsPropriedades Globais Meta
 * @param {String} projectId - Object Call Values View Output Returns Scope Arrays Objects Functions Outputs Maps Model Execution Handle Methods Data Variables Returns Rendering Return Variable Mapping Action Variables State Variables Displays Execution Flow Loop Layout Method App Returns Outputs Variables Arrays Call Component State String Formatting Check Methods Action Layout Setup Results Map Output Output Components Run Arrays Displays Action Arrays Return Array Map Model Loop Handle Code Logic Methods Fetch Layout Return Output Execution Result Displays Logic Variables Outputs View Formatting Target Flow Control String Process Event Return Code Methods Arrays Mapping Model Array Map Code Component Mapping Setup Results Maps Mapping Prop Methods Object Method Values Call Setup Output Methods Map Object App Flow Process Exec Prop Object Fetch Model Handle Results Properties Handling Variable Rendering Display Returns Mapping Array Handling Regex String Value Flow Flow Formatting Outputs Fetch Return Array Output Method Props Outputs Map Control Array Outputs Fetch Target Check Result Component Map Handle Component Action Fetch Match Rendering Object Fetch Maps Array Formats Map Methods Formats Return Execution Handle Display Logic Object Logic Map Mapping Layout Target Return Component Call Control Pattern App State Variables Formatting Format View Loop Execute Handling Fetch Formatting Scope Execute Array Component Action Format View App Setup Value Run Mapping Mapping Method Flow Component Run App Check Display Props Target ValuesID
 * @returns {Promise}
 */
export function getProject(projectId) {
  return service({
    url: `/graph/project/${projectId}`,
    method: 'get'
  })
}
