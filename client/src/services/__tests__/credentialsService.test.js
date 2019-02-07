import moxios from 'moxios';
import credentialsService from '../credentialsService';

describe('CredentialsService', () => {
  beforeEach(() => {
    moxios.install();

    moxios.stubRequest(/\/credentials.*?/, {
      status: 200,
      responseText: 'success',
      timeout: 1
    });
  });

  afterEach(() => {
    moxios.uninstall();
  });

  it('should export a specific number of methods and classes', () => {
    expect(Object.keys(credentialsService)).toHaveLength(6);
  });

  it('should have specific methods', () => {
    expect(credentialsService.addCredential).toBeDefined();
    expect(credentialsService.deleteCredential).toBeDefined();
    expect(credentialsService.deleteCredentials).toBeDefined();
    expect(credentialsService.getCredential).toBeDefined();
    expect(credentialsService.getCredentials).toBeDefined();
    expect(credentialsService.updateCredential).toBeDefined();
  });

  it('should return promises for every method', done => {
    const promises = Object.keys(credentialsService).map(value => credentialsService[value]());

    Promise.all(promises).then(success => {
      expect(success.length).toEqual(Object.keys(credentialsService).length);
      done();
    });
  });
});
