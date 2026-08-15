const { MongoClient, ObjectId } = require("mongodb");
class MongoDB {
    constructor(database) {
        // this.uri = "mongodb://127.0.0.1:27017";
        this.uri = "mongodb+srv://prajwalkulkarni01:zHLNFYN-KvmJ75W@prodject.lgxin4n.mongodb.net/?retryWrites=true&w=majority";
        this.client = new MongoClient(this.uri, {
            useUnifiedTopology: true,
            useNewUrlParser: true,
        });
        this.database = database;
        this.client.connect();
        this.db = this.client.db(this.database);
    }

    async startSession() {
        return await this.client.startSession();
    }

    async getDocs(collectionName, searchObj = {}) {
        const collection = this.db.collection(collectionName);
        let cursorFind = collection.find(searchObj);
        let docs = await cursorFind.toArray();
        return docs;
    }

    async getDoc(collectionName, searchObj) {
        const collection = this.db.collection(collectionName);
        let cursorFind = await collection.findOne(searchObj);
        return cursorFind;
    }

    async deleteDoc(collectionName, searchObj) {
        if (!searchObj) return false;
        let deletedResult = await this.db
            .collection(collectionName)
            .deleteMany(searchObj);
        return deletedResult.acknowledged;
    }

    async updateDoc(collectionName, searchObj, body) {
        try {
            body = Object.assign({}, body);
            let updatedResult = await this.db.collection(collectionName).updateOne(searchObj, { $set: body });
            return updatedResult;
        } catch (error) {
            if (error.code === 11000) {
                // Duplicate key error
                throw new Error("Duplicate key error. The update would create a duplicate document.");
            }
            throw error;
        }
    }

    async addDoc(collectionName, body) {
        try {
            body._id = body._id ? body._id : new ObjectId().toString();
            let insertedResult = await this.db.collection(collectionName).insertOne(body);
            return insertedResult;
        } catch (error) {
            if (error.code === 11000) {     // Duplicate key error
                throw new Error("The document already exists.");
            }
            throw error;
        }
    }

    async getMarks() {
        let resultClassAllocation = await this.getDocs("Class Allocation");
        let resultClasses = await this.getDocs("Class");
        let resultMarks = await this.getDocs("Marks");
        let resultStudents = await this.getDocs("Student");
        let resultSubjects = await this.getDocs("Subject");
        let resultDepartments = await this.getDocs("Department");

        let result = resultDepartments.map((department) => {
            //Adding classes to department
            department.Classes = [];
            resultClasses.forEach((classObj) => {
                if (department._id == classObj.Department) {

                    //Adding Subjects to classes
                    classObj.Subjects = [];
                    resultSubjects.forEach((subject) => {
                        if (subject.Department == department._id && subject.Semester == classObj.Semester) {
                            // Adding Students to classes
                            subject.Students = [];
                            resultStudents.forEach((student) => {
                                resultClassAllocation.forEach((ca) => {
                                    if (ca.Student == student._id &&
                                        student.Department == department._id &&
                                        ca.Class == classObj._id) {

                                        // Adding marks to each student in each subject
                                        student["Marks Gained"] = {};
                                        resultMarks.forEach((marks) => {
                                            if (marks.Subject == subject._id && marks.Student == student._id) {
                                                student["Marks Gained"] = { ...marks };
                                            }
                                        });
                                        subject.Students.push({ ...student });
                                    }
                                });
                            });
                            classObj.Subjects.push({ ...subject });
                        }
                    });
                    department.Classes.push({ ...classObj });
                }
            });
            return department;
        });

        return result;
    }

    async deleteThenInsert(collectionName, queryToDelete, insertsArray) {
        for (let i in insertsArray) insertsArray[i]['_id'] = (new ObjectId).toString();
        let collection = this.db.collection(collectionName)
        return ((await collection.deleteMany(queryToDelete)).acknowledged && (await collection.insertMany(insertsArray)).acknowledged);
    }

    async getStudents() {
        let resultStudents = await this.getDocs("Student");
        let resultClasses = await this.getDocs("Class");
        let resultClassAllocations = await this.getDocs("Class Allocation");
        let resultDepartments = await this.getDocs("Department");

        let result = resultDepartments.map(department => {
            department.Classes = [];
            resultClasses.forEach(classObj => {
                if (department._id == classObj.Department) {
                    classObj.Students = [];
                    resultStudents.forEach(student => {
                        resultClassAllocations.forEach(ca => {
                            if (ca.Student == student._id &&
                                student.Department == department._id &&
                                ca.Class == classObj._id) {
                                classObj.Students.push({ ...student });
                            }
                        })
                    });
                    department.Classes.push({ ...classObj });
                }
            });
            return department;
        });
        return result;
    }
}

const mongo = new MongoDB("projectdb");

module.exports = mongo;
