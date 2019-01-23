import { toastNotificationsReducer } from '../toastNotificationsReducer';
import { toastNotificationTypes as types } from '../../constants';

describe('toastNotificationsReducer', () => {
  it('should return the initial state', () => {
    expect(toastNotificationsReducer.initialState).toBeDefined();
  });

  it('should handle specific defined types', () => {
    const specificTypes = [types.TOAST_ADD, types.TOAST_REMOVE, types.TOAST_PAUSE, types.TOAST_RESUME];

    specificTypes.forEach(value => {
      const dispatched = {
        type: value
      };

      const resultState = toastNotificationsReducer(undefined, dispatched);

      expect({ type: value, result: resultState }).toMatchSnapshot(`defined type ${value}`);
    });
  });

  it('should handle adding and removing toast notifications', () => {
    let dispatched = {
      type: types.TOAST_ADD,
      header: 'Lorem',
      message: 'Lorem ipsum dolor',
      alertType: 'success'
    };

    let resultState = toastNotificationsReducer(undefined, dispatched);
    resultState = toastNotificationsReducer(resultState, dispatched);

    expect(resultState).toMatchSnapshot('toast added');

    dispatched = {
      type: types.TOAST_REMOVE,
      toast: resultState.toasts[0]
    };

    resultState = toastNotificationsReducer(resultState, dispatched);
    expect(resultState).toMatchSnapshot('toast removed');
  });
});
