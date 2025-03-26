[
  {
    "questions": "query_job_mask",
    "user_prompt": "What is the job mask for ProductX in EnvironmentY?",
    "context": "The system contains job masks mapped to products in different environments. A job mask is a unique identifier assigned to a product's deployment within a specific environment.",
    "expected_response": "The job mask for ProductX in EnvironmentY is JM-12345."
  },
  {
    "questions": "query_job_mask",
    "user_prompt": "Retrieve the job mask for ProductX in EnvironmentZ.",
    "context": "Job masks are assigned per product and environment. If no job mask exists, a new one may need to be registered.",
    "expected_response": "No job mask found for ProductX in EnvironmentZ. Would you like to register one?"
  },
  {
    "questions": "query_job_mask",
    "user_prompt": "Retrieve the job mask for InvalidProduct in EnvironmentY.",
    "context": "Ensure the product exists in the database before querying its job mask.",
    "expected_response": "Error: Product 'InvalidProduct' does not exist. Please check the product name and try again."
  },
  {
    "questions": "register_job_mask",
    "user_prompt": "I want to register a job mask for ProductX in EnvironmentY with Seal123.",
    "context": "Job masks must be registered with a valid product and environment. Additionally, the provided seal must be valid and unique.",
    "expected_response": "Job mask JM-56789 has been successfully registered for ProductX in EnvironmentY with Seal123."
  },
  {
    "questions": "register_job_mask",
    "user_prompt": "I want to register a job mask in EnvironmentY with Seal123.",
    "context": "A valid product is required to register a job mask along with an environment and seal.",
    "expected_response": "Error: Please specify the product along with the environment and seal to complete the job mask registration."
  },
  {
    "questions": "register_job_mask",
    "user_prompt": "I want to register a job mask for ProductX.",
    "context": "A valid environment and seal are required to register a job mask along with the product.",
    "expected_response": "Error: Please specify both the environment and seal to complete the job mask registration."
  },
  {
    "questions": "update_seal",
    "user_prompt": "Update the seal for JobMask-12345 in EnvironmentY for ProductX to Seal789.",
    "context": "A job mask in an environment may have an associated seal. The seal can be updated if the job mask exists, the product is valid, and the new seal is recognized.",
    "expected_response": "The seal for JobMask-12345 in EnvironmentY for ProductX has been successfully updated to Seal789."
  },
  {
    "questions": "update_seal",
    "user_prompt": "Update the seal for JobMask-99999 in EnvironmentY for ProductX to Seal789.",
    "context": "Ensure the job mask exists in the specified environment and is associated with the correct product before updating its seal.",
    "expected_response": "Error: Job mask 'JobMask-99999' does not exist in EnvironmentY for ProductX. Please check the job mask and try again."
  },
  {
    "questions": "update_seal",
    "user_prompt": "Update the seal for JobMask-12345 in EnvironmentY for ProductX to InvalidSeal.",
    "context": "Seals must be valid and exist in the system before they can be assigned to a job mask. The job mask must also be associated with the correct product.",
    "expected_response": "Error: The seal 'InvalidSeal' is not recognized. Please provide a valid seal."
  },
  {
    "questions": "update_seal",
    "user_prompt": "Update the seal for JobMask-12345 in EnvironmentY.",
    "context": "A product and a new seal must be specified for the update to proceed.",
    "expected_response": "Error: Please specify both the product and the new seal to update the job mask."
  },
  {
    "questions": "update_seal",
    "user_prompt": "Update the seal for JobMask-12345 for ProductX.",
    "context": "A valid environment and a new seal must be provided for the update to proceed.",
    "expected_response": "Error: Please specify both the environment and the new seal to update the job mask."
  }
]
