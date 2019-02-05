import moxios from 'moxios';
import statusService from '../statusService';

describe('StatusService', () => {
  beforeEach(() => {
    moxios.install();

    moxios.stubRequest(/\/status.*?/, {
      status: 200,
      responseText: 'success',
      timeout: 1
    });
  });

  afterEach(() => {
    moxios.uninstall();
  });

  it('should export a specific number of methods and classes', () => {
    expect(Object.keys(statusService)).toHaveLength(1);
  });

  it('should have specific methods', () => {
    expect(statusService.getStatus).toBeDefined();
  });

  it('should return promises for every method', done => {
    const promises = Object.keys(statusService).map(value => statusService[value]());

    Promise.all(promises).then(success => {
      expect(success.length).toEqual(Object.keys(statusService).length);
      done();
    });
  });
});
