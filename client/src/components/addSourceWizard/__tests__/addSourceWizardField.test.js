import React from 'react';
import { mount } from 'enzyme';
import { AddSourceWizardField } from '../addSourceWizardField';

describe('AddSourceWizardField Component', () => {
  it('should render', () => {
    const props = { id: 'test' };

    const component = mount(
      <AddSourceWizardField {...props}>
        <input id="test" type="text" value="" readOnly />
      </AddSourceWizardField>
    );

    expect(component.render()).toMatchSnapshot('render');
    expect(
      component
        .find('label')
        .at(0)
        .render()
    ).toMatchSnapshot('label');
  });
});
