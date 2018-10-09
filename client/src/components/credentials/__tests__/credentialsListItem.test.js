import React from 'react';
import configureMockStore from 'redux-mock-store';
import { mount } from 'enzyme';
import CredentialListItem from '../credentialListItem';
import { viewTypes } from '../../../redux/constants';

describe('CredentialListItem Component', () => {
  const generateEmptyStore = () =>
    configureMockStore()({ credentials: {}, viewOptions: { [viewTypes.CREDENTIALS_VIEW]: {} } });

  it('should render a basic component with a credential type', () => {
    const store = generateEmptyStore();
    const props = {
      item: {
        id: 1,
        cred_type: 'network'
      }
    };

    const component = mount(<CredentialListItem {...props} />, { context: { store } });

    expect(component.render()).toMatchSnapshot();
  });
});
