import promiseMiddleware from 'redux-promise-middleware';
import { applyMiddleware, combineReducers, createStore } from 'redux';
import moxios from 'moxios';
import { scansReducer } from '../../reducers';
import { scansActions } from '..';

describe('ScansActions', () => {
  const middleware = [promiseMiddleware()];
  const generateStore = () =>
    createStore(
      combineReducers({
        scans: scansReducer
      }),
      applyMiddleware(...middleware)
    );

  beforeEach(() => {
    moxios.install();

    moxios.wait(() => {
      const request = moxios.requests.mostRecent();
      request.respondWith({
        status: 200,
        response: {
          test: 'success'
        }
      });
    });
  });

  afterEach(() => {
    moxios.uninstall();
  });

  it('Should return response content for addScan method', done => {
    const store = generateStore();
    const dispatcher = scansActions.addScan();

    dispatcher(store.dispatch).then(() => {
      const response = store.getState().scans;

      expect(response.action.add).toEqual(true);
      done();
    });
  });

  it('Should return response content for getScan method', done => {
    const store = generateStore();
    const dispatcher = scansActions.getScan();

    dispatcher(store.dispatch).then(() => {
      const response = store.getState().scans;

      expect(response.detail.scan.test).toEqual('success');
      done();
    });
  });

  it('Should return response content for getScans method', done => {
    const store = generateStore();
    const dispatcher = scansActions.getScans();

    dispatcher(store.dispatch).then(() => {
      const response = store.getState().scans;

      expect(response.view.fulfilled).toEqual(true);
      done();
    });
  });

  it('Should return response content for updateScan method', () => {
    const dispatcher = scansActions.updateScan();

    expect(dispatcher).toBeDefined();
  });

  it('Should return response content for updatePartialScan method', () => {
    const dispatcher = scansActions.updatePartialScan();

    expect(dispatcher).toBeDefined();
  });

  it('Should return response content for deleteScan method', done => {
    const store = generateStore();
    const dispatcher = scansActions.deleteScan();

    dispatcher(store.dispatch).then(() => {
      const response = store.getState().scans;

      expect(response.update.delete).toEqual(true);
      done();
    });
  });

  it('Should return response content for startScan method', done => {
    const store = generateStore();
    const dispatcher = scansActions.startScan();

    dispatcher(store.dispatch).then(() => {
      const response = store.getState().scans;

      expect(response.action.start).toEqual(true);
      done();
    });
  });

  it('Should return response content for getScanJobs method', done => {
    const store = generateStore();
    const dispatcher = scansActions.getScanJobs();

    dispatcher(store.dispatch).then(() => {
      const response = store.getState().scans;

      expect(response.jobs.fulfilled).toEqual(true);
      done();
    });
  });

  it('Should return response content for getScanJob method', () => {
    const dispatcher = scansActions.getScanJob();

    expect(dispatcher).toBeDefined();
  });

  it('Should return response content for getConnectionScanResults method', done => {
    const store = generateStore();
    const dispatcher = scansActions.getConnectionScanResults();

    dispatcher(store.dispatch).then(() => {
      const response = store.getState().scans;

      expect(response.connectionResults.fulfilled).toEqual(true);
      done();
    });
  });

  it('Should return response content for getInspectionScanResults method', done => {
    const store = generateStore();
    const dispatcher = scansActions.getInspectionScanResults();

    dispatcher(store.dispatch).then(() => {
      const response = store.getState().scans;

      expect(response.inspectionResults.fulfilled).toEqual(true);
      done();
    });
  });

  it('Should return response content for pauseScan method', done => {
    const store = generateStore();
    const dispatcher = scansActions.pauseScan();

    dispatcher(store.dispatch).then(() => {
      const response = store.getState().scans;

      expect(response.action.pause).toEqual(true);
      done();
    });
  });

  it('Should return response content for cancelScan method', done => {
    const store = generateStore();
    const dispatcher = scansActions.cancelScan();

    dispatcher(store.dispatch).then(() => {
      const response = store.getState().scans;

      expect(response.action.cancel).toEqual(true);
      done();
    });
  });

  it('Should return response content for restartScan method', done => {
    const store = generateStore();
    const dispatcher = scansActions.restartScan();

    dispatcher(store.dispatch).then(() => {
      const response = store.getState().scans;

      expect(response.action.restart).toEqual(true);
      done();
    });
  });
});
