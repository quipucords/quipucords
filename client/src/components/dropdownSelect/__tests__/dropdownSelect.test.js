import React from 'react';
import { mount } from 'enzyme';
import DropdownSelect from '../dropdownSelect';
import { MenuItem } from 'patternfly-react';

describe('DropdownSelect Component', function() {
  it('should render', () => {
    const props = {
      id: 'testing',
      title: 'test title'
    };

    const component = mount(
      <DropdownSelect {...props}>
        <MenuItem key="one">One</MenuItem>
      </DropdownSelect>
    );

    expect(component.render()).toMatchSnapshot();
  });
});
