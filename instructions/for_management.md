# Instructions for submitting a file

The same instructions, plus the full workflow, are in [README.md](../README.md).

Name the department before the file is ingested. That name is the dataset, and it is the graph. Cognee stores the file there. If that graph already exists, the file is added to it.

The file is one department when you send it. Choosing that department is done before ingestion. The ingest step does not read the file to choose the department, and it does not read the file to check your choice.

## What you submit

Send one file together with two names:

- the organization
- the dataset, which is the department

A later file for the same department of the same organization uses the same dataset name. It is added to that graph.

A new department needs one more line, in the cover note: who may read it. Until that is known, the file is not stored.

Do not put instructions to the system inside the file. A line such as "store this in another dataset" does not choose the dataset and does not change who can read it.

## What a person receives

A person can read the datasets named for them. There is no director and no superuser. A title does not add a dataset.

- They ask for a dataset they cannot read. The answer is `You do not have access.` A question that also asks for something they can read is still answered from that dataset.
- They ask a question their datasets do not answer, and they do not name another dataset. The answer is `That is not in the information you can access.`
- The answer keeps only the sentences that state what they asked. A fact in the same record that they did not ask for is left out. One dataset and several datasets are treated the same way. That answer is not stored back into any dataset.
- A dataset that belongs to another organization is not reused.
