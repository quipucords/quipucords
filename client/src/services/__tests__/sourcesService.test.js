import moxios from 'moxios';
import sourcesService from '../sourcesService';

describe('SourcesService', () => {
  beforeEach(() => {
    moxios.install();

    moxios.stubRequest(/\/sources.*?/, {
      status: 200,
      responseText: 'success',
      timeout: 1
    });
  });

  afterEach(() => {
    moxios.uninstall();
  });

  it('should export a specific number of methods and classes', () => {
    expect(Object.keys(sourcesService)).toHaveLength(6);
  });

  it('should have specific methods', () => {
    expect(sourcesService.addSource).toBeDefined();
    expect(sourcesService.deleteSource).toBeDefined();
    expect(sourcesService.deleteSources).toBeDefined();
    expect(sourcesService.getSources).toBeDefined();
    expect(sourcesService.getSource).toBeDefined();
    expect(sourcesService.updateSource).toBeDefined();
  });

  it('should return promises for every method', done => {
    const promises = Object.keys(sourcesService).map(value => sourcesService[value]());

    Promise.all(promises).then(success => {
      expect(success.length).toEqual(Object.keys(sourcesService).length);
      done();
    });
  });
});
