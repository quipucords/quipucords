import moxios from 'moxios';
import factsService from '../factsService';

describe('FactsService', () => {
  beforeEach(() => {
    moxios.install();

    moxios.stubRequest(/\/facts.*?/, {
      status: 200,
      responseText: 'success',
      timeout: 1
    });
  });

  afterEach(() => {
    moxios.uninstall();
  });

  it('should export a specific number of methods and classes', () => {
    expect(Object.keys(factsService)).toHaveLength(1);
  });

  it('should have specific methods', () => {
    expect(factsService.addFacts).toBeDefined();
  });

  it('should return promises for every method', done => {
    const promises = Object.keys(factsService).map(value => factsService[value]());

    Promise.all(promises).then(success => {
      expect(success.length).toEqual(Object.keys(factsService).length);
      done();
    });
  });
});
