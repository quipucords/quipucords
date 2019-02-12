import moxios from 'moxios';
import reportsService from '../reportsService';

describe('ReportsService', () => {
  beforeEach(() => {
    moxios.install();

    moxios.stubRequest(/\/reports.*?/, {
      status: 200,
      responseText: 'success',
      timeout: 1
    });
  });

  afterEach(() => {
    moxios.uninstall();
  });

  it('should export a specific number of methods and classes', () => {
    expect(Object.keys(reportsService)).toHaveLength(7);
  });

  it('should have specific methods', () => {
    expect(reportsService.getReportDetails).toBeDefined();
    expect(reportsService.getReportDetailsCsv).toBeDefined();
    expect(reportsService.getReportSummary).toBeDefined();
    expect(reportsService.getReportSummaryCsv).toBeDefined();
    expect(reportsService.getMergedScanReportDetailsCsv).toBeDefined();
    expect(reportsService.getMergedScanReportSummaryCsv).toBeDefined();
    expect(reportsService.mergeScanReports).toBeDefined();
  });

  it('should return promises for every method', done => {
    const promises = Object.keys(reportsService).map(value => reportsService[value]());

    Promise.all(promises).then(success => {
      expect(success.length).toEqual(Object.keys(reportsService).length);
      done();
    });
  });
});
