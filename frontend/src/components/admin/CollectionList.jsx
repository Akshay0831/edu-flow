import React, { useState, useEffect } from "react";
import { toast } from "react-toastify";
import { Link, useLocation } from "react-router-dom";
import serverRequest from "../../helper/serverRequest";
import { InfinitySpin } from 'react-loader-spinner'
import { Button, ButtonGroup, Card, Col, Modal, Row, Table, Tab, Tabs } from 'react-bootstrap';
import { DatatableWrapper, Filter, Pagination, PaginationOptions, TableBody, TableHeader } from 'react-bs-datatable';

const toasts = (message, type) => {
    type(message, {
        position: "top-center",
        autoClose: 2500,
        hideProgressBar: false,
        closeOnClick: true,
        pauseOnHover: true,
        draggable: true,
        progress: undefined,
        theme: "colored",
    });
}

const MetaData = {
    "CO PO Map": {
        headers: [
            // { checkbox: { idProp: '_id' }, prop: 'checkbox' },
            // { isFilterable: false, isSortable: false, prop: '_id', title: 'ID' },
            { isFilterable: true, isSortable: true, prop: 'Subject', title: 'Subject' },
            { isFilterable: true, isSortable: true, prop: 'CO', title: 'CO' },
            { isFilterable: true, isSortable: true, prop: 'PO', title: 'PO' },
            { isFilterable: true, isSortable: true, prop: 'Value', title: 'Value' },
        ],
        bodyParseFunc: (json) => {
            for (let doc of json)
                for (let col in doc) {
                    if (col == "Subject" && doc[col]) doc[col] = `${doc[col]["Subject Name"]} (${doc[col]["Subject Code"]})`;
                }
            return json;
        }
    },
    Class: {
        headers: [
            // { checkbox: { idProp: '_id' }, prop: 'checkbox' },
            // { isFilterable: false, isSortable: false, prop: '_id', title: 'ID' },
            { isFilterable: true, isSortable: true, prop: 'Department', title: 'Department' },
            { isFilterable: true, isSortable: true, prop: 'Semester', title: 'Semester' },
            { isFilterable: true, isSortable: true, prop: 'Section', title: 'Section' },
        ],
        bodyParseFunc: (json) => {
            for (let doc of json)
                for (let col in doc)
                    if (col == "Department" && doc[col]) doc[col] = doc[col]["Department Name"];
            return json;
        }
    },
    "Class Allocation": {
        headers: [
            // { checkbox: { idProp: '_id' }, prop: 'checkbox' },
            // { isFilterable: false, isSortable: false, prop: '_id', title: 'ID' },
            { isFilterable: true, isSortable: true, prop: 'Class', title: 'Class' },
            { isFilterable: true, isSortable: true, prop: 'Student', title: 'Student' },
        ],
        bodyParseFunc: async (json) => {
            let depts = await (await serverRequest("http://localhost:8000/" + "documents/Department")).json();
            for (let doc of json)
                for (let col in doc) {
                    if (col == "Class" && doc[col]) {
                        let deptId = doc[col]["Department"];
                        doc[col] = `${doc[col]["Semester"]}${doc[col]["Section"]} (${depts.find(dept => dept._id == deptId)["Department Name"]})`;
                    }
                    else if (col == "Student" && doc[col]) doc[col] = `${doc[col]["Student Name"]} (${doc[col]["USN"]})`;
                }
            return json;
        }
    },
    Department: {
        headers: [
            // { checkbox: { idProp: '_id' }, prop: 'checkbox' },
            // { isFilterable: false, isSortable: false, prop: '_id', title: 'ID' },
            { isFilterable: true, isSortable: true, prop: 'Department Name', title: 'Name' },
            { isFilterable: true, isSortable: false, prop: 'HoD', title: 'Head of Department' },
        ],
        bodyParseFunc: (json) => {
            for (let doc of json)
                for (let col in doc)
                    if (col == "HoD" && doc[col]) doc[col] = `${doc[col]["Teacher Name"]} (${doc[col]["Mail"]})`;
            return json;
        }
    },
    Feedback: {
        headers: [
            // { checkbox: { idProp: '_id' }, prop: 'checkbox' },
            // { isFilterable: false, isSortable: false, prop: '_id', title: 'ID' },
            { isFilterable: true, isSortable: true, prop: 'Subject', title: 'Subject' },
            { isFilterable: true, isSortable: false, prop: 'values', title: 'Feedback' },
        ],
        bodyParseFunc: (json) => {
            for (let doc of json)
                for (let col in doc)
                    if (col == "Subject" && doc[col]) doc[col] = `${doc[col]["Subject Name"]} (${doc[col]["Subject Code"]})`;
                    else if (col == "values" && doc[col]) doc[col] = JSON.stringify(doc[col]);
            return json;
        }
    },
    Marks: {
        headers: [
            // { checkbox: { idProp: '_id' }, prop: 'checkbox' },
            // { isFilterable: false, isSortable: false, prop: '_id', title: 'ID' },
            { isFilterable: true, isSortable: true, prop: 'Student', title: 'Student' },
            { isFilterable: true, isSortable: true, prop: 'Subject', title: 'Subject' },
            { isFilterable: true, isSortable: false, prop: 'Marks Gained', title: 'Marks Gained' },
        ],
        bodyParseFunc: (json) => {
            for (let doc of json)
                for (let col in doc) {
                    if (col == "Student" && doc[col]) doc[col] = `${doc[col]["Student Name"]} (${doc[col]["USN"]})`;
                    else if (col == "Subject" && doc[col]) doc[col] = `${doc[col]["Subject Name"]} (${doc[col]["Subject Code"]})`;
                    else if (col == "Marks Gained" && doc[col]) doc[col] = JSON.stringify(doc["Marks Gained"]);
                }
            return json;
        }
    },
    Student: {
        headers: [
            // { checkbox: { idProp: '_id' }, prop: 'checkbox' },
            // { isFilterable: false, isSortable: false, prop: '_id', title: 'ID' },
            { isFilterable: true, isSortable: true, prop: 'USN', title: 'USN' },
            { isFilterable: true, isSortable: true, prop: 'Student Name', title: 'Name' },
            { isFilterable: true, isSortable: true, prop: 'Department', title: 'Department' },
            { isFilterable: true, isSortable: true, prop: 'Admission Year', title: 'Admitted' },
            { isFilterable: true, isSortable: true, prop: 'Batch', title: 'Batch' },
        ],
        bodyParseFunc: (json) => {
            for (let doc of json)
                for (let col in doc)
                    if (col == "Department" && doc[col]) doc[col] = doc[col]["Department Name"];
            return json;
        }
    },
    Subject: {
        headers: [
            // { checkbox: { idProp: '_id' }, prop: 'checkbox' },
            // { isFilterable: false, isSortable: false, prop: '_id', title: 'ID' },
            { isFilterable: true, isSortable: true, prop: 'Scheme Code', title: 'Scheme Code' },
            { isFilterable: true, isSortable: true, prop: 'Subject Code', title: 'Subject Code' },
            { isFilterable: true, isSortable: true, prop: 'Subject Name', title: 'Name' },
            { isFilterable: true, isSortable: true, prop: 'Semester', title: 'Semester' },
            { isFilterable: false, isSortable: false, prop: 'Max Marks', title: 'Max Marks' },
            { isFilterable: true, isSortable: true, prop: 'Department', title: 'Department' },
        ],
        bodyParseFunc: (json) => {
            for (let doc of json)
                for (let col in doc) {
                    if (col == "Max Marks" && doc[col]) doc[col] = JSON.stringify(doc["Max Marks"]);
                    else if (col == "Department" && doc[col]) doc[col] = doc[col]["Department Name"];
                }
            return json;
        }
    },
    Teacher: {
        headers: [
            // { checkbox: { idProp: '_id' }, prop: 'checkbox' },
            // { isFilterable: false, isSortable: false, prop: '_id', title: 'ID' },
            { isFilterable: true, isSortable: true, prop: 'Teacher Name', title: 'Name' },
            { isFilterable: true, isSortable: true, prop: 'Mail', title: 'Mail ID' },
            { isFilterable: true, isSortable: true, prop: 'Department', title: 'Department' },
            { isFilterable: true, isSortable: false, prop: 'Role', title: 'Role' },
        ],
        bodyParseFunc: (json) => {
            for (let doc of json)
                for (let col in doc)
                    if (col == "Department" && doc[col]) doc[col] = doc[col]["Department Name"];
            return json;
        }
    },
    "Teacher Allocation": {
        headers: [
            // { checkbox: { idProp: '_id' }, prop: 'checkbox' },
            // { isFilterable: false, isSortable: false, prop: '_id', title: 'ID' },
            { isFilterable: true, isSortable: true, prop: 'Teacher', title: 'Teacher' },
            { isFilterable: true, isSortable: true, prop: 'Subject', title: 'Subject Code' },
            { isFilterable: true, isSortable: false, prop: 'Class', title: 'Class' },
            { isFilterable: true, isSortable: true, prop: 'Department', title: 'Department' },
        ],
        bodyParseFunc: (json) => {
            for (let doc of json)
                for (let col in doc) {
                    if (col == "Teacher" && doc[col]) doc[col] = `${doc[col]["Teacher Name"]} (${doc[col]["Mail"]})`;
                    else if (col == "Subject" && doc[col]) doc[col] = `${doc[col]["Subject Name"]} (${doc[col]["Subject Code"]})`;
                    else if (col == "Class" && doc[col]) doc[col] = `${doc[col]["Semester"]}${doc[col]["Section"]}`;
                    else if (col == "Department" && doc[col]) doc[col] = doc[col]["Department Name"];
                }
            return json;
        }
    },
};

export default function CollectionList() {
    const serverURL = 'http://localhost:8000/';
    document.title = "Collection List";

    const location = useLocation();
    const [collectionSelected, setCollectionSelected] = useState(location.state || "Teacher");
    const [deleteRow, setDeleteRow] = useState("");
    const [documents, setDocuments] = useState([]);
    const [showSpinner, setShowSpinner] = useState(false);

    useEffect(() => {
        const abortController = new AbortController();
        const signal = abortController.signal;

        const fetchData = async () => {
            try {
                setShowSpinner(true);
                console.log("Called API: " + serverURL + collectionSelected);
                setDocuments(await MetaData[collectionSelected].bodyParseFunc(await (await serverRequest(serverURL + collectionSelected, "GET", {}, { signal })).json()));
                setShowSpinner(false);
            } catch (error) {
                console.log(error.message);
            }
        }

        fetchData();

        return () => {
            abortController.abort();
        };
    }, [collectionSelected]);

    const deleteDocument = (id) => {
        serverRequest(serverURL + collectionSelected, "DELETE", { _id: id })
            .then((res) => {
                console.log("Called API: Delete " + id);
                if (res.status == 200) {
                    toasts(`Deleted Teacher`, toast.success);
                    setDocuments(documents.filter((doc) => doc._id !== id));
                }
            })
            .catch((err) => toasts("Error:" + err.message, toast.error));
    }

    const handleDeleteModalClose = () => setDeleteRow("");

    return (
        <main className="pt-5">
            <Modal show={deleteRow} onHide={handleDeleteModalClose} backdrop="static" keyboard={false}>
                <Modal.Header closeButton>
                    <Modal.Title>Confirm Delete Document</Modal.Title>
                </Modal.Header>
                <Modal.Body> DELETE from {collectionSelected.toUpperCase()} : <br /> {Object.values(deleteRow).join(', ')} </Modal.Body>
                <Modal.Footer>
                    <Button variant="secondary" onClick={handleDeleteModalClose}>
                        Close
                    </Button>
                    <Button variant="primary" onClick={() => { deleteDocument(deleteRow._id); handleDeleteModalClose() }}>Delete</Button>
                </Modal.Footer>
            </Modal>
            <div className="container">
                <Card>
                    <Card.Header className="fs-3">Collections CRUD</Card.Header>
                    <Tabs id="documentsSelector" activeKey={collectionSelected} onSelect={(collectionKey) => { setCollectionSelected(collectionKey) }}>
                        {Object.keys(MetaData).map(collection => {
                            return <Tab eventKey={collection} key={collection} title={collection} />
                        })}
                    </Tabs>

                    <Card.Body className="table-responsive overflow-auto">
                        {showSpinner ? <div style={{ display: 'flex', alignContent: 'center', justifyContent: 'center' }}><InfinitySpin
                            color="#000"
                            width='200'
                            visible={true}
                        /></div> :
                            <DatatableWrapper
                                body={documents}
                                headers={
                                    MetaData[collectionSelected]["headers"].concat([{
                                        prop: "button",
                                        title: (<Link to={`/admin/${collectionSelected}/add`}><Button style={{ width: '90%' }} size="sm" variant="success"><i className="fa fa-plus" /></Button></Link>),
                                        cell: (row) => (
                                            <ButtonGroup aria-label="DB Actions" style={{ width: '90%' }} >
                                                <Link to={`/admin/${collectionSelected}/update/${row['_id']}`} className="btn btn-warning btn-sm"><i className="fa fa-pencil" /></Link>
                                                <Button variant="danger" size="sm" onClick={() => setDeleteRow(row)}><i className="fa fa-trash" /></Button>
                                            </ButtonGroup>
                                        )
                                    }])
                                }

                                paginationOptionsProps={{
                                    initialState: {
                                        options: [10, 20, 40, 80, 120],
                                        rowsPerPage: 10
                                    }
                                }}
                            >
                                <Row className="mb-4">
                                    <Col className="d-flex flex-col justify-content-end align-items-end" lg={4} xs={12}>
                                        <Filter />
                                    </Col>
                                    <Col className="d-flex flex-col justify-content-lg-center align-items-center justify-content-sm-start" lg={4} sm={6} xs={12} >
                                        <PaginationOptions alwaysShowPagination />
                                    </Col>
                                    <Col className="d-flex flex-col justify-content-end align-items-end" lg={4} sm={6} xs={12}>
                                        <Pagination alwaysShowPagination />
                                    </Col>
                                </Row>
                                <Table bordered striped hover>
                                    <TableHeader />
                                    <TableBody>
                                    </TableBody>
                                </Table>
                            </DatatableWrapper>
                        }
                    </Card.Body>
                </Card>
            </div>
        </main>
    );
}