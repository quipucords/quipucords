import cx from 'classnames';
import React from 'react';

import { Button, ListViewInfoItem } from 'patternfly-react';

// TODO make this make more sense for VerticalNavigation

export const navItems = [
  {
    title: 'Sources',
    description: 'Sources'
  },
  {
    title: 'Scans',
    description: 'Scans'
  }
];

export const renderActions = () => (
  <div>
    <Button>Details</Button>
  </div>
);

export const renderAdditionalInfoItems = itemProperties => {
  return (
    itemProperties &&
    Object.keys(itemProperties).map(prop => {
      const classNames = cx('pficon', {
        'pficon-flavor': prop === 'hosts',
        'pficon-cluster': prop === 'clusters',
        'pficon-container-node': prop === 'nodes',
        'pficon-image': prop === 'images'
      });
      return (
        <ListViewInfoItem key={prop}>
          <span className={classNames} />
          <strong>{itemProperties[prop]}</strong> {prop}
        </ListViewInfoItem>
      );
    })
  );
};
