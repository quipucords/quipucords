import promiseMiddleware from 'redux-promise-middleware';
import { applyMiddleware, combineReducers, createStore } from 'redux';
import moxios from 'moxios';
import { reportsReducer } from '../../reducers';
import { reportsActions } from '..';

describe('ReportsActions', () => {
  const middleware = [promiseMiddleware()];
  const generateStore = () =>
    createStore(
      combineReducers({
        reports: reportsReducer
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

  it('Should return response content for getReportSummary method', done => {
    const store = generateStore();
    const dispatcher = reportsActions.getReportSummary();

    dispatcher(store.dispatch).then(() => {
      const response = store.getState().reports;

      expect(response.report.reports.test).toEqual('success');
      done();
    });
  });

  it('Should return response content for getReportSummaryCsv method', done => {
    const store = generateStore();
    const dispatcher = reportsActions.getReportSummaryCsv();

    dispatcher(store.dispatch).then(() => {
      const response = store.getState().reports;

      expect(response.report.fulfilled).toEqual(true);
      done();
    });
  });

  it('Should return response content for getReportDetails method', done => {
    const store = generateStore();
    const dispatcher = reportsActions.getReportDetails();

    dispatcher(store.dispatch).then(() => {
      const response = store.getState().reports;

      expect(response.report.reports.test).toEqual('success');
      done();
    });
  });

  it('Should return response content for getReportDetailsCsv method', done => {
    const store = generateStore();
    const dispatcher = reportsActions.getReportDetailsCsv();

    dispatcher(store.dispatch).then(() => {
      const response = store.getState().reports;

      expect(response.report.fulfilled).toEqual(true);
      done();
    });
  });

  it('Should return response content for getMergedScanReportSummaryCsv method', done => {
    const store = generateStore();
    const dispatcher = reportsActions.getMergedScanReportSummaryCsv();

    dispatcher(store.dispatch).then(() => {
      const response = store.getState().reports;

      expect(response.report.fulfilled).toEqual(true);
      done();
    });
  });

  it('Should return response content for getMergedScanReportDetailsCsv method', done => {
    const store = generateStore();
    const dispatcher = reportsActions.getMergedScanReportDetailsCsv();

    dispatcher(store.dispatch).then(() => {
      const response = store.getState().reports;

      expect(response.report.fulfilled).toEqual(true);
      done();
    });
  });

  it('Should return response content for mergeScanReports method', done => {
    const store = generateStore();
    const dispatcher = reportsActions.mergeScanReports();

    dispatcher(store.dispatch).then(() => {
      const response = store.getState().reports;

      expect(response.merge.fulfilled).toEqual(true);
      done();
    });
  });
});
