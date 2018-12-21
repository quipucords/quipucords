import moxios from 'moxios';
import userService from '../userService';

describe('UserService', () => {
  beforeEach(() => {
    moxios.install();

    moxios.stubRequest(/\/users.*?/, {
      status: 200,
      responseText: 'success',
      timeout: 1
    });
  });

  afterEach(() => {
    moxios.uninstall();
  });

  it('should export a specific number of methods and classes', () => {
    expect(Object.keys(userService)).toHaveLength(2);
  });

  it('should have specific methods', () => {
    expect(userService.whoami).toBeDefined();
    expect(userService.logoutUser).toBeDefined();
  });

  it('should return promises for every method', done => {
    const promises = Object.keys(userService).map(value => userService[value]());

    Promise.all(promises).then(success => {
      expect(success.length).toEqual(Object.keys(userService).length);
      done();
    });
  });
});
