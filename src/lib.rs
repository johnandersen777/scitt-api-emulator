use log::info;
use uuid::Uuid;
use pyo3::prelude::*;
use pyo3::types::PyTuple;
use pyo3::exceptions::PyValueError;
use serde::{Deserialize, Serialize};
use serde_json;
use std::fmt;
use std::collections::HashMap;


// Wrapper type for serde_json::Error
struct SerdeErrorWrapper(serde_json::Error);

// Implement From<serde_json::Error> for the wrapper type
impl From<serde_json::Error> for SerdeErrorWrapper {
    fn from(err: serde_json::Error) -> SerdeErrorWrapper {
        SerdeErrorWrapper(err)
    }
}

// Implement From<SerdeErrorWrapper> for PyErr
impl From<SerdeErrorWrapper> for PyErr {
    fn from(wrapper: SerdeErrorWrapper) -> PyErr {
        PyValueError::new_err(wrapper.0.to_string())
    }
}

#[derive(Serialize, Deserialize, Debug, Clone)]
struct Context {
    config: HashMap<String, HashMap<String, String>>,
    secrets: HashMap<String, String>,
}

#[derive(Serialize, Deserialize, Debug)]
struct WorkflowJobStep {
    uses: Option<String>,
}

#[derive(Serialize, Deserialize, Debug)]
struct WorkflowJob {
    #[serde(rename = "runs-on")]
    runs_on: String,
    steps: Vec<WorkflowJobStep>,
}

#[derive(Serialize, Deserialize, Debug)]
struct Workflow {
    on: HashMap<String, HashMap<String, Vec<String>>>,
    jobs: HashMap<String, WorkflowJob>,
}

#[derive(Serialize, Deserialize, Debug)]
enum PolicyEngineCompleteExitStatuses {
    #[serde(rename = "success")]
    Success,
    #[serde(rename = "failure")]
    Failure,
}

#[derive(Serialize, Deserialize, Debug)]
struct PolicyEngineComplete {
    id: String,
    exit_status: PolicyEngineCompleteExitStatuses,
    outputs: HashMap<String, serde_json::Value>,
    annotations: HashMap<String, serde_json::Value>,
}

#[derive(Serialize, Deserialize, Debug)]
enum PolicyEngineStatuses {
    #[serde(rename = "submitted")]
    Submitted,
    #[serde(rename = "in_progress")]
    InProgress,
    #[serde(rename = "complete")]
    Complete,
    #[serde(rename = "unknown")]
    Unknown,
    #[serde(rename = "input_validation_error")]
    InputValidationError,
}

#[derive(Serialize, Deserialize, Debug)]
struct PolicyEngineStatusUpdateJobStep {
    status: PolicyEngineStatuses,
    metadata: HashMap<String, String>,
    outputs: HashMap<String, serde_json::Value>,
}

#[derive(Serialize, Deserialize, Debug)]
struct PolicyEngineStatusUpdateJob {
    steps: HashMap<String, PolicyEngineStatusUpdateJobStep>,
}

#[derive(Serialize, Deserialize, Debug)]
struct PolicyEngineInProgress {
    id: String,
    status_updates: HashMap<String, PolicyEngineStatusUpdateJob>,
}

#[derive(Serialize, Deserialize, Debug)]
struct PolicyEngineSubmitted {
    id: String,
}

#[derive(Serialize, Deserialize, Debug)]
struct PolicyEngineUnknown {
    id: String,
}

#[derive(Serialize, Deserialize, Debug)]
struct PolicyEngineInputValidationError {
    msg: String,
    loc: Vec<String>,
    #[serde(rename = "type")]
    error_type: String,
    url: Option<String>,
    input: Option<String>,
}

#[derive(Serialize, Deserialize, Debug)]
struct PolicyEngineWorkflowJobStep {
    #[serde(rename = "if")]
    if_condition: Option<String>,
    name: Option<String>,
    uses: Option<String>,
    shell: Option<String>,
    #[serde(rename = "with")]
    with_inputs: HashMap<String, String>,
    env: HashMap<String, String>,
    run: Option<String>,
}

#[derive(Serialize, Deserialize, Debug)]
struct PolicyEngineWorkflowJob {
    #[serde(rename = "runs-on")]
    runs_on: serde_json::Value,
    steps: Option<Vec<PolicyEngineWorkflowJobStep>>,
}

#[derive(Serialize, Deserialize, Debug)]
struct PolicyEngineWorkflow {
    name: Option<String>,
    on: serde_json::Value,
    jobs: HashMap<String, PolicyEngineWorkflowJob>,
}

#[derive(Serialize, Deserialize, Debug)]
struct PolicyEngineRequest {
    inputs: HashMap<String, serde_json::Value>,
    workflow: PolicyEngineWorkflow,
    context: HashMap<String, serde_json::Value>,
    stack: HashMap<String, serde_json::Value>,
}



#[derive(Debug)]
struct StringError(String);

impl fmt::Display for StringError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "{}", self.0)
    }
}

impl std::error::Error for StringError {}

impl From<String> for StringError {
    fn from(err: String) -> StringError {
        StringError(err)
    }
}

#[derive(Debug)]
enum ValidationError {
    MissingField(StringError),
    CustomError(StringError),
}

// pyo3::exceptions::impl_native_exception!(ValidationError, pyo3::exceptions::PyExc_Exception, pyo3:exceptions::native_doc!("ValidationError"));

// Convert serde_json::Error to PyErr
impl From<ValidationError> for PyErr {
    fn from(err: ValidationError) -> PyErr {
        PyValueError::new_err(err.to_string())
    }
}


impl fmt::Display for ValidationError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match *self {
            ValidationError::MissingField(ref err) => write!(f, "Missing field: {}", err),
            ValidationError::CustomError(ref err) => write!(f, "Custom error: {}", err),
        }
    }
}

impl std::error::Error for ValidationError {
    fn source(&self) -> Option<&(dyn std::error::Error + 'static)> {
        match *self {
            ValidationError::MissingField(ref err) => Some(err),
            ValidationError::CustomError(ref err) => Some(err),
        }
    }
}

fn validate_status(status: &PolicyEngineStatuses) -> Result<(), ValidationError> {
    match status {
        PolicyEngineStatuses::Unknown => Err(ValidationError::CustomError(
            "Unknown status is not allowed.".to_string().into(),
        )),
        _ => Ok(()),
    }
}

fn validate_id(id: &str) -> Result<(), ValidationError> {
    if id.is_empty() {
        Err(ValidationError::MissingField(
            "id is required and cannot be empty.".to_string().into(),
        ))
    } else {
        Ok(())
    }
}

fn validate_workflow(_workflow: &PolicyEngineWorkflow) -> Result<(), ValidationError> {
    Ok(())
}

#[derive(Serialize, Deserialize, Debug)]
struct PolicyEngineStatus {
    id: String,
    status: PolicyEngineStatuses,
    detail: HashMap<String, serde_json::Value>,
}

impl PolicyEngineStatus {
    pub fn new(
        id: String,
        status: PolicyEngineStatuses,
        detail: HashMap<String, serde_json::Value>,
    ) -> Result<Self, ValidationError> {
        validate_status(&status)?;
        validate_id(&id)?;
        Ok(PolicyEngineStatus { id, status, detail })
    }
}

impl PolicyEngineWorkflow {
    pub fn validate(&self) -> Result<(), ValidationError> {
        validate_workflow(self)?;
        Ok(())
    }
}


#[pyfunction]
fn parse_policy_engine_request(_py: Python<'_>, json_data: &str) -> PyResult<()> {
    Python::with_gil(|py| -> PyResult<()> {
        let fun: Py<PyAny> = PyModule::from_code_bound(
            py,
            "def example(*args, **kwargs):
                if args:
                    raise Execption(args[0])
                    print(args[0])
                print(args, kwargs)
                print('Workflow validated successfully.')",
            "",
            "",
        )?
        .getattr("example")?
        .into();

        // call object with Python tuple of positional arguments
        let args = PyTuple::new_bound(py, &[json_data]);
        fun.call1(py, args)?;

        let decoded: PolicyEngineRequest = serde_json::from_str(json_data).map_err(SerdeErrorWrapper)?;
        println!("Decoded JSON: {:#?}", decoded);

        // call object without any arguments
        fun.call0(py)?;

        let status = PolicyEngineStatuses::Submitted;
        let detail = HashMap::new();

        let policy_status = PolicyEngineStatus::new(Uuid::new_v4().to_string(), status, detail)?;
        println!(
            "Created PolicyEngineStatus successfully with status: {:?}",
            policy_status.status
        );

        let workflow = PolicyEngineWorkflow {
            name: Some("example_workflow".to_string()),
            on: serde_json::Value::String("push".to_string()),
            jobs: HashMap::new(),
        };

        workflow.validate()?;
        println!("Workflow validated successfully.");

        Ok(())
    })
}

#[pymodule]
fn scitt_api_emulator_rust_policy_engine(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    pyo3_log::init();

    m.add_function(wrap_pyfunction!(parse_policy_engine_request, m)?)?;

    Ok(())
}
